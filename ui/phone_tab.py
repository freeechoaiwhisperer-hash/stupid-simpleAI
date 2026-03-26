# ============================================================
#  FreedomForge AI — ui/phone_tab.py
#  Phone companion panel — scan QR, chat from your phone.
# ============================================================

import io
import threading

import customtkinter as ctk
from PIL import Image, ImageTk

from core import phone_bridge
from assets.i18n import t


class PhonePanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app   = app
        self.theme = theme
        self._qr_photo = None   # keep reference so GC doesn't collect it
        self._build()

    # ── Build ─────────────────────────────────────────────────

    def _build(self):
        T = self.theme

        # ── Header ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(22, 0))

        ctk.CTkLabel(
            hdr,
            text="📱  Phone Companion",
            font=("Arial", 22, "bold"),
            text_color=T["gold"],
            anchor="w",
        ).pack(side="left")

        # Status badge
        self._status_lbl = ctk.CTkLabel(
            hdr,
            text="● offline",
            font=("Arial", 12, "bold"),
            text_color=T["text_dim"],
        )
        self._status_lbl.pack(side="right", padx=8)

        # ── Card ──────────────────────────────────────────────
        card = ctk.CTkFrame(
            self,
            fg_color=T["bg_card"],
            corner_radius=16,
        )
        card.pack(fill="both", expand=True, padx=24, pady=16)

        # ── Left: instructions ─────────────────────────────────
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            left,
            text="Chat from your phone",
            font=("Arial", 17, "bold"),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text=(
                "Your AI stays private — it never leaves your home network.\n"
                "No cloud. No subscriptions. No accounts.\n\n"
                "How to connect:\n"
                "  1.  Make sure your phone is on the same Wi-Fi.\n"
                "  2.  Press Start below.\n"
                "  3.  Scan the QR code with your phone camera.\n"
                "  4.  Start chatting!"
            ),
            font=("Arial", 13),
            text_color=T["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=340,
        ).pack(anchor="w", pady=(10, 0))

        # URL label
        self._url_lbl = ctk.CTkLabel(
            left,
            text="",
            font=("Arial", 13, "bold"),
            text_color=T["accent"],
            anchor="w",
            cursor="hand2",
        )
        self._url_lbl.pack(anchor="w", pady=(16, 0))
        self._url_lbl.bind("<Button-1>", self._open_browser)

        # Start / Stop button
        self._btn = ctk.CTkButton(
            left,
            text="▶  Start Companion",
            font=("Arial", 14, "bold"),
            height=44,
            corner_radius=12,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            command=self._toggle,
        )
        self._btn.pack(anchor="w", pady=(20, 0))

        # Port note
        ctk.CTkLabel(
            left,
            text="Runs on port 11435 — local network only.",
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(anchor="w", pady=(8, 0))

        # ── Right: QR code ─────────────────────────────────────
        right = ctk.CTkFrame(
            card,
            fg_color=T["bg_panel"],
            corner_radius=12,
            width=220,
        )
        right.pack(side="right", fill="y", padx=28, pady=24)
        right.pack_propagate(False)

        ctk.CTkLabel(
            right,
            text="Scan to connect",
            font=("Arial", 12, "bold"),
            text_color=T["text_secondary"],
        ).pack(pady=(16, 8))

        self._qr_canvas = ctk.CTkLabel(
            right,
            text="📱\n\nPress Start\nto generate\nQR code",
            font=("Arial", 12),
            text_color=T["text_dim"],
            width=200,
            height=200,
        )
        self._qr_canvas.pack(padx=10, pady=4)

        ctk.CTkLabel(
            right,
            text="Same Wi-Fi required",
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(pady=(8, 16))

    # ── Actions ───────────────────────────────────────────────

    def _toggle(self):
        T = self.theme
        if phone_bridge.is_running():
            phone_bridge.stop()
            self._btn.configure(
                text="▶  Start Companion",
                fg_color=T["accent"],
                hover_color=T["accent_hover"],
            )
            self._status_lbl.configure(text="● offline", text_color=T["text_dim"])
            self._url_lbl.configure(text="")
            self._qr_canvas.configure(
                image=None,
                text="📱\n\nPress Start\nto generate\nQR code",
            )
        else:
            url = phone_bridge.start()
            self._btn.configure(
                text="■  Stop Companion",
                fg_color=T.get("red", "#c0392b"),
                hover_color=T.get("red_hover", "#a93226"),
            )
            self._status_lbl.configure(
                text="● live", text_color=T.get("green", "#2ecc71"))
            self._url_lbl.configure(text=f"🌐  {url}")
            # Generate QR in background so UI doesn't freeze
            threading.Thread(target=self._load_qr, daemon=True).start()

    def _load_qr(self):
        img = phone_bridge.make_qr_image(size=200)
        if img is None:
            self.after(0, lambda: self._qr_canvas.configure(
                image=None,
                text=(
                    "QR unavailable.\n"
                    "Install: pip install qrcode[pil]\n\n"
                    f"Open manually:\n{phone_bridge.get_url()}"
                ),
            ))
            return
        # Convert to CTkImage so it renders correctly on HiDPI
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img,
                               size=(200, 200))
        self._qr_photo = ctk_img   # prevent GC
        self.after(0, lambda: self._qr_canvas.configure(
            image=ctk_img, text=""))

    def _open_browser(self, _=None):
        if phone_bridge.is_running():
            import webbrowser
            webbrowser.open(phone_bridge.get_url())

    # ── Refresh when switching to this tab ────────────────────

    def refresh(self):
        T = self.theme
        if phone_bridge.is_running():
            self._status_lbl.configure(
                text="● live", text_color=T.get("green", "#2ecc71"))
            self._btn.configure(
                text="■  Stop Companion",
                fg_color=T.get("red", "#c0392b"),
                hover_color=T.get("red_hover", "#a93226"),
            )
            self._url_lbl.configure(text=f"🌐  {phone_bridge.get_url()}")
