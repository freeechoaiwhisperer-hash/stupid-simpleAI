# ⚒️ FreedomForge AI — AI Prompt Library

> **How to use this file:**
> Each section below is a complete, self-contained prompt.
> Copy everything between the `--- START PROMPT ---` and `--- END PROMPT ---`
> markers and paste it directly into DeepSeek, Gemini, Claude, ChatGPT,
> or any other AI you are using to help build this app.
>
> The prompts include all the context the AI needs — no extra explanation required.

---

## Table of Contents

1. [File Cleaner UI Panel](#1-file-cleaner-ui-panel)
2. [Real ComfyUI Wan2.1 Video Workflow](#2-real-comfyui-wan21-video-workflow)
3. [Chat Memory Stats in Privacy Panel](#3-chat-memory-stats-in-privacy-panel)
4. [Control Key UI in Settings](#4-control-key-ui-in-settings)
5. [Forge Tool Library Chat Commands](#5-forge-tool-library-chat-commands)
6. [Sandbox VM One-Click Setup](#6-sandbox-vm-one-click-setup)
7. [System Health Check Module](#7-system-health-check-module)
8. [Document Editor Module](#8-document-editor-module)
9. [Multi-Model Chat (Models Talk to Each Other)](#9-multi-model-chat-models-talk-to-each-other)
10. [Plugin Builder — Describe It, AI Builds It](#10-plugin-builder--describe-it-ai-builds-it)

---
---

## 1. File Cleaner UI Panel

> **What this gives you:** A full "Files" tab in the app sidebar so users can
> scan a folder, see what would be sorted, organise everything into typed
> sub-folders, and restore if they change their mind.
> The backend is already written — this is only the UI wrapper.

```
--- START PROMPT ---

I am building FreedomForge AI — a free, fully local, private AI desktop app
built in Python with customtkinter.  I need you to write one new file.

───────────────────────────────────────────────
PROJECT CONTEXT
───────────────────────────────────────────────

The app uses a sidebar + panels pattern.  Each panel is a ctk.CTkFrame subclass
that lives in the ui/ folder.  Panels receive (master, app, theme) arguments.
The theme is a plain dict — key colours you will use:

  T["bg_card"]         # card background
  T["bg_panel"]        # section background
  T["text_primary"]    # white-ish
  T["text_secondary"]  # grey
  T["text_dim"]        # dimmer grey
  T["gold"]            # gold accent #FFD700
  T["accent"]          # main button colour
  T["accent_hover"]    # main button hover

The panel is registered in ui/app.py like this:

  from ui.file_cleaner_tab import FileCleanerPanel
  # inside _build_ui():
  self.cleaner_panel = FileCleanerPanel(self.content_frame, self, T)
  self.panels["Files"] = self.cleaner_panel
  # nav button: ("🗂️", "Files", "Files")

───────────────────────────────────────────────
THE BACKEND (already written — do NOT modify it)
───────────────────────────────────────────────

File: plugins/echo_file_sort_cleaner.py
Key public functions:

  from plugins.echo_file_sort_cleaner import (
      scan,               # scan(directory_str) -> ScanResult
      make_snapshot,      # make_snapshot(ScanResult, snapshot_path) -> Path
      organise,           # organise(ScanResult, output_dir, on_progress=cb) -> list of (src,dst)
      restore_from_snapshot,  # restore_from_snapshot(snapshot_path) -> (count, errors)
  )

  ScanResult has:
    .scan_dir    str
    .entries     list of FileEntry
    .duplicates  list of lists (groups of duplicate file paths)

  FileEntry has:
    .original_path  str
    .category       str  ("images","videos","audio","documents","code","archives","misc")
    .size_bytes     int
    .sha256         str
    .moved_to       str or None

Snapshots are saved to: Path.home() / ".free_echo" / "snapshots"

───────────────────────────────────────────────
WHAT I NEED YOU TO WRITE
───────────────────────────────────────────────

New file: ui/file_cleaner_tab.py

The panel must have these five sections, each in a card (rounded ctk.CTkFrame):

SECTION 1 — Folder Picker
  - A "Choose Folder" button that opens filedialog.askdirectory()
  - A label showing the selected path (grey when nothing selected)

SECTION 2 — Scan
  - "Scan" button that runs scan() in a background thread
  - While scanning, show a spinner label ("Scanning…")
  - After scan, show a results card:
      "Found X files · Y duplicate groups · Z MB total"
  - Disable all other buttons until scan is done

SECTION 3 — Preview
  - After a scan, show a scrollable list of what would be moved:
      "images/photo.jpg   (was /home/user/Desktop/photo.jpg)"
  - Show first 50 entries max with "…and X more" at the bottom
  - Empty state: "Run a scan to see a preview"

SECTION 4 — Organise
  - "Organise" button
  - Before organising, call make_snapshot() and save the snapshot path
  - Run organise() in a background thread, passing on_progress= callback
    that updates a progress label in the UI
  - When done, show "✅ Done — X files sorted, Y duplicates moved to /duplicates/"
  - Disable button while running

SECTION 5 — Restore
  - "Restore from Snapshot" button
  - Show a confirmation dialog ("This will move everything back. Continue?")
  - Run restore_from_snapshot() in a background thread
  - Show result: "✅ Restored X files" or "⚠️ X errors"
  - Disabled if no snapshot has been made this session

STYLE RULES:
  - Match the style of ui/privacy_tab.py exactly
  - Use self._section(parent, text) for section headers
  - Use self._card(parent) to create section cards
  - All heavy work runs in daemon threads; UI updates use self.after(0, lambda: ...)
  - No blocking the main thread

Please write the complete ui/file_cleaner_tab.py file.
Include a _section() and _card() helper method at the bottom, matching
the pattern used in other panels.

--- END PROMPT ---
```

---
---

## 2. Real ComfyUI Wan2.1 Video Workflow

> **What this gives you:** Replaces the placeholder stub in `modules/video.py`
> with a real working ComfyUI node graph for Wan2.1 text-to-video.

```
--- START PROMPT ---

I am building FreedomForge AI — a free, local, private AI desktop app.
I need you to rewrite one specific function in an existing file.

───────────────────────────────────────────────
THE CURRENT FILE: modules/video.py  (partial)
───────────────────────────────────────────────

COMFY_URL = "http://127.0.0.1:8188"

def generate_video(prompt, generator="wan2.1", on_result=None,
                   on_error=None, on_status=None):
    def _generate():
        if not is_comfyui_running():
            on_error("ComfyUI is not running.")
            return
        on_status("Sending prompt to ComfyUI...")
        workflow = _build_workflow(prompt, generator)
        r = requests.post(f"{COMFY_URL}/prompt",
                          json={"prompt": workflow}, timeout=10)
        if r.status_code != 200:
            on_error(f"ComfyUI error: {r.status_code}")
            return
        prompt_id = r.json().get("prompt_id")
        on_status(f"Generating... (ID: {prompt_id})")
        on_result(f"✅ Started. Check ComfyUI at {COMFY_URL}")
    threading.Thread(target=_generate, daemon=True).start()

def _build_workflow(prompt: str, generator: str) -> dict:
    # ← THIS IS THE STUB — needs to be replaced
    return {
        "1": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 1]},
        },
    }

───────────────────────────────────────────────
WHAT I NEED YOU TO DO
───────────────────────────────────────────────

1. Replace _build_workflow() with a real Wan2.1 text-to-video node graph
   that ComfyUI will actually accept and run.

   The workflow should:
   - Include a proper CLIPTextEncode node for positive prompt
   - Include a CLIPTextEncode node for negative prompt
     (default negative: "blurry, low quality, watermark, text")
   - Include KSampler with sane defaults (steps=20, cfg=7.5, sampler="euler")
   - Include VAEDecode
   - Include SaveImage (output goes to ComfyUI's standard output folder)
   - For generator=="wan2.1": use the standard Wan2.1 model checkpoint name
     "wan2.1_t2v_14B_fp8.safetensors" (or the most common file name)
   - For generator=="animatediff": include AnimateDiff nodes instead

2. After submitting the workflow to /prompt, poll /history/{prompt_id}
   every 2 seconds in the background thread.
   - Call on_status("Generating… step X/20") as progress updates come in
   - When history shows status=="success", call on_result() with the output
     image/video filename from the history response
   - If status=="error", call on_error() with the error message

3. Add a sensible negative_prompt parameter to generate_video()
   with default value: "blurry, low quality, watermark, text, distorted"

Return the complete updated modules/video.py file.
Keep all existing code — only replace _build_workflow() and update
generate_video() to add polling and the negative_prompt parameter.

--- END PROMPT ---
```

---
---

## 3. Chat Memory Stats in Privacy Panel

> **What this gives you:** A "🧠 Chat Memory" section in the Privacy tab
> that shows how much the AI remembers about you, lets you clear it,
> and lets you mark things as important.

```
--- START PROMPT ---

I am building FreedomForge AI.  I need you to add a new section to an
existing UI panel file.

───────────────────────────────────────────────
THE MEMORY MANAGER API (core/memory_manager.py)
───────────────────────────────────────────────

from core.memory_manager import get_memory_manager

mm = get_memory_manager()
stats = mm.stats()
# stats is a dict:
# {
#   "rolling_entries": int,    # recent messages kept verbatim
#   "summary_entries": int,    # older messages compressed to summaries
#   "memory_dir": str,         # path to memory folder on disk
# }

mm.clear()                     # deletes all rolling + summaries from disk
mm.mark_important(text: str)   # adds a "system" entry flagged important=True
                                # so it is never auto-compressed

───────────────────────────────────────────────
CURRENT STRUCTURE OF ui/privacy_tab.py (_build method)
───────────────────────────────────────────────

def _build(self):
    T = self.theme
    scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

    # ... header ...

    self._section(scroll, "🔑  Data Encryption")
    self._build_encryption(self._card(scroll))

    self._section(scroll, "🛡️  VPN Protection")
    self._build_vpn(self._card(scroll))

    self._section(scroll, "⚡  Network Kill Switch")
    self._build_kill(self._card(scroll))

    self._section(scroll, "📡  Port Monitor")
    self._build_ports(self._card(scroll))

    self._section(scroll, "🐛  Crash Reports")
    self._build_crashes(self._card(scroll))

    # ← ADD THE MEMORY SECTION HERE (at the bottom)

───────────────────────────────────────────────
WHAT I NEED YOU TO WRITE
───────────────────────────────────────────────

Add a new method _build_memory(self, parent) to ui/privacy_tab.py.

The section header should be: "🧠  Chat Memory"

Inside the card, show:

ROW 1 — Stats display (auto-refreshes when section opens)
  "Rolling messages:  42"      ← mm.stats()["rolling_entries"]
  "Memory summaries:  8"       ← mm.stats()["summary_entries"]
  "Memory folder:  ~/.free_echo/memory/"  ← mm.stats()["memory_dir"]
  These should be labels that you can refresh. Store them as self._mem_*

ROW 2 — Clear button
  Red "🗑  Clear All Memory" button
  On click: show a ctk.CTkToplevel confirmation dialog
  ("This deletes everything the AI remembers about you. Continue?")
  If confirmed: call mm.clear(), then refresh the stats labels

ROW 3 — Mark Important
  A single-line text field + "⭐ Mark as Important" button side by side
  On click: call mm.mark_important(text_field.get()), clear the field,
  briefly show "✅ Saved" next to the button for 2 seconds

Then add this line to the bottom of _build():
  self._section(scroll, "🧠  Chat Memory")
  self._build_memory(self._card(scroll))

Return only the new _build_memory() method and the two new lines to add
to _build().  Show where in _build() to insert the two lines.

Use the same code style as the existing panel.  All colours come from
self.theme (T).

--- END PROMPT ---
```

---
---

## 4. Control Key UI in Settings

> **What this gives you:** A "🔑 Control Key" section in Settings so users
> can set a personal password that locks agent mode.

```
--- START PROMPT ---

I am building FreedomForge AI.  I need you to add a new section to
ui/settings.py and a small change to ui/app.py.

───────────────────────────────────────────────
THE CONTROL KEY API (modules/security_guard.py)
───────────────────────────────────────────────

from modules.security_guard import get_control_key

ck = get_control_key()

ck.is_set          # bool — True if a key has been configured
ck.set_key(text)   # hash and store a new key
ck.verify(text)    # bool — True if text matches stored key
ck.clear_key(text) # bool — removes key IF text matches current key

───────────────────────────────────────────────
CURRENT ui/settings.py structure (overview)
───────────────────────────────────────────────

class SettingsPanel(ctk.CTkFrame):
    def _build(self):
        # scroll = ctk.CTkScrollableFrame
        # sections: Language, Theme, Font, Model Params, Reset
        # each section: self._section(scroll, "Header")
        #               self._build_xxx(self._card(scroll))

───────────────────────────────────────────────
TASK 1 — Add _build_control_key() to ui/settings.py
───────────────────────────────────────────────

Add a new section "🔑  Control Key" at the END of _build(), before Reset.

The section should show TWO different UIs based on whether a key is set:

STATE A — No key set (ck.is_set == False):
  - Text: "No control key is set.  Set one to lock agent mode."
  - A password entry field (show=*)
  - "Set Key" button → calls ck.set_key(entry.get()), refreshes section

STATE B — Key is set (ck.is_set == True):
  - Text: "🔒 Control key is active."
  - A password entry field (show=*)
  - "Verify" button → calls ck.verify(entry.get()),
      shows "✅ Correct" or "❌ Wrong key" for 2 seconds
  - "Remove Key" button → calls ck.clear_key(entry.get()),
      shows "✅ Key removed" if True, "❌ Wrong key" if False,
      then refreshes section

Call this method from _build() like the other sections.

───────────────────────────────────────────────
TASK 2 — Gate agent mode with the control key (ui/app.py)
───────────────────────────────────────────────

In ui/app.py, find the method _toggle_agent() (it toggles agent mode on/off).

When the user tries to ENABLE agent mode, check the control key:
  from modules.security_guard import get_control_key
  ck = get_control_key()
  if ck.is_set:
      # Show a small ctk.CTkInputDialog asking for the key
      key = ctk.CTkInputDialog(text="Enter control key to enable agent mode:",
                               title="Control Key").get_input()
      if not ck.verify(key or ""):
          # Show an error and return without enabling agent mode
          # (you can use a short-lived label or a messagebox)
          return

When the user DISABLES agent mode, no check is needed — always allow.

Return:
1. The new _build_control_key() method for settings.py
2. The updated _toggle_agent() method for app.py
Include clear comments showing where to add each piece.

--- END PROMPT ---
```

---
---

## 5. Forge Tool Library Chat Commands

> **What this gives you:** `/forge list`, `/forge run`, `/forge delete`,
> `/forge info` — chat commands that let users manage the AI's built-in
> tool library from the chat window.

```
--- START PROMPT ---

I am building FreedomForge AI.  I need you to create one new file and
add a few lines to two existing files.

───────────────────────────────────────────────
THE TOOL REPO API (core/tool_repo.py)
───────────────────────────────────────────────

from core.tool_repo import get_tool_repo

repo = get_tool_repo()

tools = repo.list_tools()
# Returns list of ToolRecord objects.
# ToolRecord has: .name, .description, .language, .path,
#                 .created_by, .created_at, .tags, .last_used_at

result = repo.run_tool(name: str)
# Returns dict: {"stdout": str, "stderr": str, "returncode": int, "path": str}

repo.delete_tool(name: str) -> bool

───────────────────────────────────────────────
HOW MODULES WORK (modules/weather.py as example template)
───────────────────────────────────────────────

Every module file has:
  MODULE_NAME = "forge"  # or whatever

  def handle(message: str,
             on_result: Callable[[str], None],
             on_error:  Callable[[str], None]) -> None:
      # parse message, do work in background thread, call on_result/on_error

Modules are triggered by patterns registered in modules/__init__.py:
  "forge": [
      r"^/forge\b",
      r"\bforge\s+(list|run|delete|info)\b",
  ]

And registered in ui/app.py with a module import line.

───────────────────────────────────────────────
WHAT I NEED YOU TO CREATE
───────────────────────────────────────────────

FILE 1: modules/forge.py

Implement handle() supporting these commands:

/forge list
  → calls repo.list_tools()
  → format as a table:
      🗂️  Forge Tool Library (N tools)
      ─────────────────────────────
      • rename_files      python  created by FreeEchoAssistant
      • sort_downloads    bash    created by user
      ...
  → if empty: "No tools yet.  Ask the AI to write a tool and it will appear here."

/forge info <name>
  → find tool by name in list_tools()
  → show: name, description, language, path, created_by, created_at, tags
  → if not found: "Tool '<name>' not found.  Use /forge list to see all tools."

/forge run <name>
  → call repo.run_tool(name)
  → show stdout (trimmed to 2000 chars if very long)
  → if returncode != 0, show stderr as an error
  → if not found: friendly error

/forge delete <name>
  → call repo.delete_tool(name)
  → confirm deletion in the reply: "✅ Tool 'name' deleted."
  → if not found: friendly error

FILE 2: modules/__init__.py  (just add trigger patterns)
  Add to the TRIGGERS dict:
    "forge": [
        r"^/forge\b",
        r"\bforge\s+(list|run|delete|info)\b",
    ]

FILE 3: ui/app.py  (just add the import and register)
  At the top with other module imports:
    import modules.forge as forge_module
  In _build_ui() where modules are registered:
    modules.register("forge", forge_module)
  (Show me the exact line to add next to the existing module registrations.)

Return all three files/snippets.

--- END PROMPT ---
```

---
---

## 6. Sandbox VM One-Click Setup

> **What this gives you:** A "🛡️ Sandbox" panel that lets the user launch
> an isolated virtual machine with one click so the AI can do things
> safely without touching the real system.

```
--- START PROMPT ---

I am building FreedomForge AI — a local, private AI desktop app in Python
with customtkinter.  I need a new core module and a new UI panel.

───────────────────────────────────────────────
FEATURE: One-Click Sandbox VM
───────────────────────────────────────────────

The goal is to let the AI run commands, scripts, and tools inside an
isolated environment that cannot touch the real system.  If anything
goes wrong inside the sandbox, the real computer is untouched.

───────────────────────────────────────────────
FILE 1: core/sandbox.py
───────────────────────────────────────────────

Write a module that:

1. Detects which VM backend is available on the current OS:
   - Linux: firejail (preferred), then bubblewrap, then a Docker container
   - Windows: Windows Sandbox (if available), then a Docker container
   - macOS: a Docker container (or show a setup guide)

2. Provides this API:

   sandbox_available() -> bool
     Returns True if any backend was found

   get_backend_name() -> str
     Returns e.g. "firejail", "docker", "windows_sandbox", "none"

   run_in_sandbox(command: str,
                  on_output: Callable[[str], None],
                  on_done:   Callable[[int], None],
                  timeout:   int = 60) -> None
     Runs *command* inside the sandbox.
     Calls on_output() for each line of stdout/stderr.
     Calls on_done(returncode) when finished.
     Runs in a daemon thread — never blocks.

   install_backend(on_status: Callable[[str], None]) -> None
     Tries to install the best available backend automatically
     (e.g. "sudo apt install firejail", "winget install Docker.DockerDesktop")
     Calls on_status() with progress messages.

3. Log all sandbox events using: from core import logger

FILE 2: ui/sandbox_tab.py
───────────────────────────────────────────────

A new panel with:

SECTION 1 — Status
  - Shows current backend: "✅ firejail is ready" or "⚠️ No sandbox found"
  - "Refresh" button to re-detect

SECTION 2 — Test
  - A text field pre-filled with "echo Hello from sandbox; ls /tmp"
  - "Run in Sandbox" button
  - Output box (scrollable ctk.CTkTextbox, read-only) showing the output

SECTION 3 — Setup (shown only when no backend found)
  - "Install Sandbox Backend" button → calls install_backend()
  - Shows progress in a small label below the button

Register in ui/app.py:
  from ui.sandbox_tab import SandboxPanel
  self.sandbox_panel = SandboxPanel(self.content_frame, self, T)
  self.panels["Sandbox"] = self.sandbox_panel
  # nav item: ("🛡️", "Sandbox", "Sandbox")

Style: match ui/privacy_tab.py.
Theme dict keys: T["bg_card"], T["text_primary"], T["text_secondary"],
                 T["gold"], T["accent"], T["accent_hover"].

Return both complete files.

--- END PROMPT ---
```

---
---

## 7. System Health Check Module

> **What this gives you:** A "🖥️ System" tab where the AI scans the user's
> computer, explains what it finds in plain English, and suggests fixes.

```
--- START PROMPT ---

I am building FreedomForge AI — a free local AI app in Python + customtkinter.

I need a new module and UI panel: System Health Check.

Goal: anyone (even non-technical users) can click one button, and the app
tells them in plain English how their computer is doing.

───────────────────────────────────────────────
FILE 1: core/system_health.py
───────────────────────────────────────────────

Use only stdlib + psutil (already a dependency).

Collect:
  - CPU: usage %, core count, model name if available
  - RAM: total, used, free, % used
  - Disk: for each mounted drive: total, used, free, % used
  - Running processes: top 5 by CPU usage (name, pid, cpu%)
  - Startup items: on Linux read /etc/xdg/autostart/*.desktop;
                   on Windows use winreg HKCU\Software\Microsoft\Windows\CurrentVersion\Run;
                   on Mac use launchctl list
  - Python version, OS name+version
  - Last boot time (human-readable)
  - Temperature: psutil.sensors_temperatures() if available

Provide:
  def collect() -> dict
    Returns a structured dict of all the above.

  def summarise(data: dict) -> list[str]
    Returns a list of plain-English observations, for example:
    - "Your RAM is 87% full — this will slow things down."
    - "Your C: drive has only 3 GB free — consider cleaning up."
    - "CPU is at 95% — something is working hard right now."
    - "12 startup programs found — these slow your boot time."
    - "Last restart: 23 days ago — a restart might help."
    Keep it friendly and non-technical.

FILE 2: ui/system_tab.py
───────────────────────────────────────────────

Panel with:

SECTION 1 — Overview cards (4 cards in a horizontal row)
  CPU card, RAM card, Disk card, Uptime card
  Each card: icon + headline number + small bar showing percentage
  These update live every 3 seconds using self.after(3000, ...)

SECTION 2 — AI Summary
  "Run Health Check" button
  Calls core/system_health.collect() and summarise() in a thread
  Shows the summary as a bulleted list (one label per bullet)
  Shows "✅ Everything looks good!" if no issues found

SECTION 3 — Top Processes
  Updated every 5 seconds
  Simple list: process name · CPU% · RAM%

Register in ui/app.py:
  from ui.system_tab import SystemPanel
  self.system_panel = SystemPanel(self.content_frame, self, T)
  self.panels["System"] = self.system_panel
  # nav item: ("🖥️", "System", "System")

Style: match ui/privacy_tab.py.  All heavy work in daemon threads.

Return both complete files.

--- END PROMPT ---
```

---
---

## 8. Document Editor Module

> **What this gives you:** A "📄 Docs" tab — a lightweight local document
> editor so users never need Word or Google Docs.

```
--- START PROMPT ---

I am building FreedomForge AI — a free, local, private AI desktop app
in Python with customtkinter.

I need a basic document editor panel.

───────────────────────────────────────────────
FILE: ui/docs_tab.py
───────────────────────────────────────────────

Build a document editor panel with:

TOOLBAR (top bar, horizontal):
  [New] [Open] [Save] [Save As] [─────] [Font size: 12 ▼] [─────]
  [Bold] [Italic] [Underline]
  [─────] [Ask AI] ← sends selected text to the chat panel for AI editing

EDITOR AREA:
  A large ctk.CTkTextbox that fills the remaining space
  Supports: typing, copy/paste, undo/redo (Ctrl+Z / Ctrl+Y)
  Font: "Arial" size 13 by default

FILE OPERATIONS:
  New — clears editor (prompts "Save first?" if unsaved changes exist)
  Open — filedialog.askopenfilename(filetypes=[("Text","*.txt"),("Markdown","*.md"),("All","*.*")])
       — reads and displays file contents
  Save — writes to current file path; if no path, does Save As
  Save As — filedialog.asksaveasfilename(defaultextension=".txt")

ASK AI:
  Gets the currently selected text (or all text if nothing selected)
  Calls self.app.send_to_chat(selected_text + "\n\n(Edit or improve this text)")
  Where send_to_chat() is a method you should add to ui/app.py that
  pre-fills the chat input and sends the message

STATUS BAR (bottom):
  Shows: filename · word count · character count · "Unsaved changes" if dirty

KEYBOARD SHORTCUTS:
  Ctrl+N = New, Ctrl+O = Open, Ctrl+S = Save, Ctrl+Shift+S = Save As

Register in ui/app.py:
  from ui.docs_tab import DocsPanel
  self.docs_panel = DocsPanel(self.content_frame, self, T)
  self.panels["Docs"] = self.docs_panel
  # nav item: ("📄", "Docs", "Docs")

Also add send_to_chat(text) to ui/app.py:
  def send_to_chat(self, text: str):
      self.switch_panel("Chat")
      self.chat_panel.set_input(text)

And add set_input(text) to ui/chat.py:
  def set_input(self, text: str):
      self._input.delete("1.0", "end")
      self._input.insert("1.0", text)

Style: match the theme dict pattern used throughout the project.
       T["bg_card"], T["bg_panel"], T["text_primary"], T["accent"], etc.

Return ui/docs_tab.py in full.
Also return the 3 small additions needed in ui/app.py and ui/chat.py.

--- END PROMPT ---
```

---
---

## 9. Multi-Model Chat (Models Talk to Each Other)

> **What this gives you:** A "🤖 Multi-AI" tab where you can load two
> different models and watch them have a conversation or debate a topic —
> the output of one becomes the input of the next.

```
--- START PROMPT ---

I am building FreedomForge AI.  I need a new panel for multi-model chat.

───────────────────────────────────────────────
EXISTING INFRASTRUCTURE
───────────────────────────────────────────────

core/model_manager.py provides:
  is_model_loaded() -> bool
  get_loaded_model_name() -> str
  generate_stream(messages, on_token, on_complete, on_error)

There is already a modules/multi_agent.py that handles /scout and /plan
commands.  This new panel is SEPARATE — a standalone multi-model
conversation tab, not a chat command.

───────────────────────────────────────────────
FILE: ui/multi_chat_tab.py
───────────────────────────────────────────────

The panel lets the user run a "ping-pong" conversation between two AI models.
Model A responds to a seed prompt.  Model A's response becomes the next
prompt for Model B.  Model B's response goes back to Model A.  Repeat.

Layout:

TOP ROW — Configuration
  [Model A: <current loaded model>]   [Model B: <dropdown of loaded models>]
  Note: for MVP, both models use the same loaded model but with different
        system prompts.  Label them "Persona A" and "Persona B" instead.

  Persona A system prompt:  text field (default: "You are a skeptical critic.")
  Persona B system prompt:  text field (default: "You are an enthusiastic optimist.")

SEED PROMPT ROW
  A text field: "Start the conversation with:"
  e.g. "Is AI good or bad for humanity?"
  [Start] button   [Stop] button

CONVERSATION DISPLAY
  A scrollable ctk.CTkTextbox showing the evolving conversation:
    [Persona A]: "AI is dangerous because..."
    [Persona B]: "But consider the benefits..."
    [Persona A]: "Those benefits are overstated..."
    ...
  Persona A messages in one colour, Persona B in another.

CONTROLS
  Max rounds: a slider 1–20 (default 6)
  When max rounds reached, conversation stops automatically

IMPLEMENTATION NOTES:
  - Use generate_stream() from core.model_manager for actual inference
  - Switch persona by changing the system message in the messages list
  - Run the ping-pong loop in a daemon thread
  - Use self.after() for all UI updates
  - Add a [Copy Full Conversation] button at the bottom

Register in ui/app.py:
  from ui.multi_chat_tab import MultiChatPanel
  self.multi_chat_panel = MultiChatPanel(self.content_frame, self, T)
  self.panels["MultiAI"] = self.multi_chat_panel
  # nav item: ("🤖", "Multi-AI", "MultiAI")

Return the complete ui/multi_chat_tab.py file.

--- END PROMPT ---
```

---
---

## 10. Plugin Builder — Describe It, AI Builds It

> **What this gives you:** A "🔧 Plugin Builder" tab where the user
> describes what they want, and the AI writes, tests, and saves a plugin —
> all with one click.

```
--- START PROMPT ---

I am building FreedomForge AI.  I need a "Plugin Builder" panel.

───────────────────────────────────────────────
THE VISION
───────────────────────────────────────────────

The user types what they want (e.g. "A tool that renames all my photos
by date taken").  The AI writes the Python code, shows it, lets the user
edit it, then saves it to the Forge Tool Library and runs a quick test.

───────────────────────────────────────────────
EXISTING INFRASTRUCTURE
───────────────────────────────────────────────

core/model_manager.py:
  generate_stream(messages, on_token, on_complete, on_error)

core/tool_repo.py:
  get_tool_repo().register_tool(name, description, language, code, created_by)
  get_tool_repo().run_tool(name) -> {"stdout":..., "stderr":..., "returncode":...}

modules/security_guard.py:
  get_control_key().verify(text) -> bool  # key gating if set

───────────────────────────────────────────────
FILE: ui/plugin_builder_tab.py
───────────────────────────────────────────────

Layout:

SECTION 1 — Describe Your Plugin
  Large text area: "What should this plugin do? Describe it in plain English."
  Example placeholder: "Rename all photos in a folder using the date they were taken."
  [Build Plugin ▶] button

SECTION 2 — Generated Code (shown after AI responds)
  Header: "Here is the plugin the AI wrote:"
  A large editable ctk.CTkTextbox pre-filled with the generated Python code
  The user can edit the code directly before saving
  [Copy] button top-right of the code box

SECTION 3 — Save & Test (shown after code is generated)
  Plugin name field (auto-filled from AI, editable)
  Plugin description field (auto-filled, editable)
  [💾 Save to Forge Library] button
    → calls tool_repo.register_tool(name, description, "python", code, "user")
    → shows "✅ Saved to /forge list"
  [▶ Test Run] button
    → calls tool_repo.run_tool(name) after saving
    → shows stdout/stderr in a small output box
    → shows "✅ Success" or "❌ Error: ..." with returncode

IMPLEMENTATION:
  When user clicks [Build Plugin ▶]:
  1. Show a spinner "🤖 Writing your plugin..."
  2. Construct this system prompt for the model:
     "You are an expert Python developer.
      Write a complete, runnable Python script for the following task.
      Output ONLY the Python code — no explanation, no markdown fences.
      The script must run standalone with python3 and print its output.
      It must handle errors gracefully."
  3. User message = whatever they typed in the description box
  4. Call generate_stream(), stream tokens into the code box
  5. When complete, auto-fill the name/description fields by calling the
     model again with: "Give this plugin a short snake_case name and
     one sentence description.  Reply as JSON: {name: ..., description: ...}"

Register in ui/app.py:
  from ui.plugin_builder_tab import PluginBuilderPanel
  self.plugin_panel = PluginBuilderPanel(self.content_frame, self, T)
  self.panels["Plugins"] = self.plugin_panel
  # nav item: ("🔧", "Plugins", "Plugins")

Style: match ui/privacy_tab.py.
All generation in daemon threads, UI updates via self.after().

Return the complete ui/plugin_builder_tab.py file.

--- END PROMPT ---
```

---

## Tips for Getting the Best Results

**General tips that work on any AI:**

1. **Paste the whole prompt** — don't summarise it. The context matters.
2. **If the AI stops early**, say: *"Continue from where you left off"*
3. **If it gets the style wrong**, say: *"Match the style of the existing files exactly — same indentation, same comment style, same method naming"*
4. **For long files**, ask: *"Write this in chunks — first the class definition and __init__, then each method separately"*
5. **If it uses wrong imports**, paste the exact import line from an existing file and say: *"Use this exact import pattern"*

**DeepSeek-specific tips:**
- DeepSeek is great at Python and GUI code. Use it for all the UI panels.
- Ask it: *"Think step by step before writing"* for complex logic

**Gemini-specific tips:**
- Gemini handles large context well — you can paste the entire existing file and say "add this to it"
- Use Gemini for the ComfyUI workflow (Prompt 2) — it's strong on API integration

**Claude-specific tips:**
- Claude follows style guidelines very precisely
- For panel code: paste the full `ui/privacy_tab.py` file along with the prompt
- Claude is best for the multi-model chat (Prompt 9) and plugin builder (Prompt 10)

---

*FreedomForge AI is dedicated to Miranda.*
*She will never be forgotten.*

*Built by Ryan Dennison.*
