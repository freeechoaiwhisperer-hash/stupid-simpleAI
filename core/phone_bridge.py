# ============================================================
#  FreedomForge AI — core/phone_bridge.py
#  Local phone companion server.
#
#  • Runs a tiny HTTP server on your LAN (never the internet).
#  • Your phone scans the QR code, opens the mobile chat page.
#  • Everything stays on your local network — private & safe.
# ============================================================

import io
import json
import os
import queue
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from core import logger

# ── Mobile chat page (single-file HTML, no external dependencies) ─────────────
_MOBILE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>FreedomForge AI</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0d0d0d;color:#e8e8e8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;height:100dvh;display:flex;flex-direction:column}
  #topbar{background:#1a1a1a;padding:14px 18px;display:flex;align-items:center;gap:10px;border-bottom:2px solid #ffd700;flex-shrink:0}
  #topbar span{font-size:1.15rem;font-weight:700;color:#ffd700}
  #status{font-size:.75rem;color:#888;margin-left:auto}
  #chat{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}
  .bubble{max-width:85%;padding:10px 14px;border-radius:16px;line-height:1.5;font-size:.95rem;white-space:pre-wrap;word-wrap:break-word}
  .user{background:#1e3a5f;align-self:flex-end;border-bottom-right-radius:4px}
  .ai{background:#1e1e1e;align-self:flex-start;border-bottom-left-radius:4px;border:1px solid #2a2a2a}
  .ai em{color:#888;font-style:normal}
  #bottom{background:#1a1a1a;padding:10px 12px;display:flex;gap:8px;border-top:1px solid #2a2a2a;flex-shrink:0}
  #inp{flex:1;background:#2a2a2a;border:none;border-radius:12px;padding:10px 14px;color:#e8e8e8;font-size:.95rem;resize:none;max-height:100px;outline:none}
  #send{background:#ffd700;color:#0d0d0d;border:none;border-radius:12px;padding:10px 18px;font-weight:700;font-size:.95rem;cursor:pointer;flex-shrink:0;touch-action:manipulation}
  #send:active{opacity:.8}
  #empty{color:#444;text-align:center;margin:auto;font-size:.9rem;padding:20px}
</style>
</head>
<body>
<div id="topbar">
  <span>⚒️ FreedomForge AI</span>
  <span id="status">● ready</span>
</div>
<div id="chat"><div id="empty">💬 Ask anything — your AI is right here on this device.</div></div>
<div id="bottom">
  <textarea id="inp" rows="1" placeholder="Message…" autocorrect="off" spellcheck="false"></textarea>
  <button id="send" onclick="send()">Send</button>
</div>
<script>
var busy = false;
var pollTimer = null;
var pollId = null;

function autosize(el){
  el.style.height='auto';
  el.style.height=Math.min(el.scrollHeight,100)+'px';
}

document.getElementById('inp').addEventListener('input',function(){autosize(this)});
document.getElementById('inp').addEventListener('keydown',function(e){
  if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}
});

function addBubble(cls,text){
  var el=document.getElementById('empty');
  if(el) el.remove();
  var d=document.createElement('div');
  d.className='bubble '+cls;
  d.textContent=text;
  var chat=document.getElementById('chat');
  chat.appendChild(d);
  chat.scrollTop=chat.scrollHeight;
  return d;
}

function setStatus(t){ document.getElementById('status').textContent=t; }

function send(){
  if(busy) return;
  var inp=document.getElementById('inp');
  var msg=inp.value.trim();
  if(!msg) return;
  inp.value=''; autosize(inp);
  addBubble('user',msg);
  busy=true;
  setStatus('● thinking…');
  var aiBubble=addBubble('ai','…');
  fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.id){
        pollId=d.id;
        pollId && poll(aiBubble);
      } else {
        aiBubble.textContent=d.reply||'(no response)';
        busy=false; setStatus('● ready');
      }
    })
    .catch(function(e){aiBubble.textContent='⚠️ Error: '+e; busy=false; setStatus('● ready');});
}

function poll(bubble){
  fetch('/poll?id='+encodeURIComponent(pollId))
    .then(function(r){return r.json();})
    .then(function(d){
      if(d.text!==undefined) bubble.textContent=d.text||'…';
      if(d.done){
        busy=false; setStatus('● ready');
      } else {
        pollTimer=setTimeout(function(){poll(bubble);},300);
      }
    })
    .catch(function(){busy=false; setStatus('● ready');});
}
</script>
</body>
</html>
"""

from typing import Optional

# ── Server state ──────────────────────────────────────────────────────────────
_server: Optional[ThreadingHTTPServer] = None
_server_thread: Optional[threading.Thread] = None
_port: int = 11435

# In-flight generation responses keyed by a short ID
_responses: dict = {}
_responses_lock = threading.Lock()
_next_id = 0


def _new_id() -> str:
    global _next_id
    _next_id += 1
    return str(_next_id)


# ── HTTP handler ──────────────────────────────────────────────────────────────
class _Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        logger.info(f"[phone] {fmt % args}")

    def _send(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8",
                       _MOBILE_HTML.encode())
        elif path == "/poll":
            self._handle_poll()
        else:
            self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/chat":
            self._handle_chat()
        else:
            self._send(404, "text/plain", b"Not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_chat(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body)
            msg    = str(data.get("message", "")).strip()
            if not msg:
                self._send(400, "application/json",
                           json.dumps({"error": "empty message"}).encode())
                return

            rid = _new_id()
            with _responses_lock:
                _responses[rid] = {"text": "", "done": False}

            # Fire generation in background
            from core import model_manager
            if not model_manager.is_model_loaded():
                with _responses_lock:
                    _responses[rid] = {"text": "⚠️  No model loaded. Please load a model in the desktop app first.", "done": True}
            else:
                def _on_token(tok):
                    with _responses_lock:
                        if rid in _responses:
                            _responses[rid]["text"] += tok

                def _on_complete():
                    with _responses_lock:
                        if rid in _responses:
                            _responses[rid]["done"] = True

                def _on_error(err):
                    with _responses_lock:
                        if rid in _responses:
                            _responses[rid]["text"] += f"\n⚠️ {err}"
                            _responses[rid]["done"] = True

                model_manager.generate_stream(
                    messages=[{"role": "user", "content": msg}],
                    on_token=_on_token,
                    on_complete=_on_complete,
                    on_error=_on_error,
                )

            self._send(200, "application/json",
                       json.dumps({"id": rid}).encode())
        except Exception as e:
            self._send(500, "application/json",
                       json.dumps({"error": str(e)}).encode())

    def _handle_poll(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            rid    = params.get("id", [None])[0]
            if rid is None:
                self._send(400, "application/json",
                           json.dumps({"error": "missing id"}).encode())
                return
            with _responses_lock:
                info = _responses.get(rid, {"text": "", "done": True})
                if info.get("done"):
                    _responses.pop(rid, None)
            self._send(200, "application/json",
                       json.dumps(info).encode())
        except Exception as e:
            self._send(500, "application/json",
                       json.dumps({"error": str(e)}).encode())


# ── Public API ────────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    """Return the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_url() -> str:
    return f"http://{get_local_ip()}:{_port}"


def is_running() -> bool:
    return _server is not None


def start(port: int = 11435) -> str:
    """Start the companion server. Returns the URL."""
    global _server, _server_thread, _port
    if _server is not None:
        return get_url()
    _port = port
    _server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    _server_thread = threading.Thread(
        target=_server.serve_forever, daemon=True)
    _server_thread.start()
    url = get_url()
    logger.info(f"Phone companion running at {url}")
    return url


def stop():
    global _server, _server_thread
    if _server:
        _server.shutdown()
        _server = None
        _server_thread = None
        logger.info("Phone companion stopped")


def make_qr_image(size: int = 200):
    """Return a PIL Image of the QR code for the companion URL, or None."""
    try:
        import qrcode  # type: ignore
        url = get_url()
        qr  = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=3,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        # Resize to requested size
        pil = img.get_image() if hasattr(img, "get_image") else img
        pil = pil.resize((size, size))
        return pil
    except ImportError:
        return None
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        return None
