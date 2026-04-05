# ============================================================
#  FreedomForge AI — ui/video_tab.py
#  Video generation panel — ComfyUI / LTX-Video installer + launcher
# ============================================================

import threading
import customtkinter as ctk
from assets.i18n import t
from modules import video_installer


class VideoPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app      = app
        self.theme    = theme
        self._installing = False
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        for w in self.winfo_children():
            w.destroy()
        self._build()

    # ── Build UI ─────────────────────────────────────────────

    def _build(self):
        T      = self.theme
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Header
        ctk.CTkLabel(
            scroll,
            text="🎬  Video Generation",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(24, 2), padx=24, anchor="w")

        ctk.CTkLabel(
            scroll,
            text="Generate videos locally using ComfyUI + LTX-Video.",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=24, anchor="w", pady=(0, 14))

        # ── Status card ──────────────────────────────────────
        self._section(scroll, "⚡  Status")
        status_card = self._card(scroll)
        self._status_row = self._row(
            status_card,
            "ComfyUI",
            "Checking…",
        )
        self._check_comfyui_status()

        # ── Install card ─────────────────────────────────────
        self._section(scroll, "📦  One-Click Install")
        inst_card = self._card(scroll)

        ctk.CTkLabel(
            inst_card,
            text=(
                "Installs ComfyUI, LTX-Video custom nodes, and the selected model\n"
                "automatically in your home directory."
            ),
            font=("Arial", 11),
            text_color=T["text_secondary"],
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=16, pady=(10, 6))

        self._install_btn = ctk.CTkButton(
            inst_card,
            text="🎬  Install Video Module",
            width=240, height=42,
            corner_radius=8,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            text_color="#ffffff",
            font=("Arial", 13, "bold"),
            command=self._start_install,
        )
        self._install_btn.pack(anchor="w", padx=16, pady=(0, 12))

        # ── Log output ───────────────────────────────────────
        self._section(scroll, "📋  Installation Log")
        log_card = self._card(scroll)

        self._log_box = ctk.CTkTextbox(
            log_card,
            height=220,
            font=("Courier", 11),
            fg_color=T["bg_deep"],
            text_color=T["green"],
            state="disabled",
        )
        self._log_box.pack(fill="x", padx=16, pady=12)

        # ── Generate card ────────────────────────────────────
        self._section(scroll, "✨  Generate a Video")
        gen_card = self._card(scroll)

        ctk.CTkLabel(
            gen_card,
            text="Prompt:",
            font=("Arial", 12),
            text_color=T["text_primary"],
        ).pack(anchor="w", padx=16, pady=(10, 0))

        self._prompt_box = ctk.CTkTextbox(
            gen_card,
            height=60,
            font=("Arial", 12),
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_width=1,
            border_color=T["border"],
            wrap="word",
        )
        self._prompt_box.pack(fill="x", padx=16, pady=(4, 0))

        ctk.CTkButton(
            gen_card,
            text="🎬  Generate",
            width=160, height=38,
            corner_radius=8,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            text_color="#ffffff",
            font=("Arial", 12, "bold"),
            command=self._generate,
        ).pack(anchor="w", padx=16, pady=10)

    # ── Installation ─────────────────────────────────────────

    def _start_install(self):
        if self._installing:
            return
        self._installing = True
        self._install_btn.configure(
            state="disabled",
            text="Installing…",
            fg_color=self.theme["bg_hover"],
        )
        self._log("🎬 Starting installation…")

        video_installer.install(
            on_log=lambda msg: self.after(0, lambda m=msg: self._log(m)),
            on_complete=lambda ok, msg: self.after(
                0, lambda: self._install_done(ok, msg)),
        )

    def _install_done(self, ok: bool, msg: str):
        self._installing = False
        T = self.theme
        if ok:
            self._install_btn.configure(
                state="normal",
                text="✅  Installed — Reinstall",
                fg_color=T["bg_hover"],
                text_color=T["green"],
            )
            self._log("\n⚡ Video module ready! Try generating a video below.")
        else:
            self._install_btn.configure(
                state="normal",
                text="❌  Retry Install",
                fg_color="#6a0000",
                text_color="#ffffff",
            )
            self._log(f"\n❌ Installation failed: {msg}")
        self._check_comfyui_status()

    def _log(self, msg: str):
        try:
            self._log_box.configure(state="normal")
            self._log_box.insert("end", msg + "\n")
            self._log_box.configure(state="disabled")
            self._log_box.see("end")
        except Exception:
            pass

    # ── ComfyUI status check ──────────────────────────────────

    def _check_comfyui_status(self):
        def _check():
            import os
            from modules.comfyui import is_comfyui_running
            running  = is_comfyui_running()
            present  = os.path.isdir(video_installer.COMFY_DIR)
            if running:
                label = "✅  Running on port 8188"
                color = self.theme["green"]
            elif present:
                label = "⚠️  Installed but not running"
                color = self.theme["yellow"]
            else:
                label = "❌  Not installed"
                color = self.theme.get("red", "#cc3333")
            self.after(0, lambda: self._update_status(label, color))

        threading.Thread(target=_check, daemon=True).start()

    def _update_status(self, text: str, color: str):
        try:
            # Replace description label in the status row
            for widget in self._status_row.winfo_children():
                children = widget.winfo_children()
                if len(children) >= 2:
                    children[1].configure(
                        text=text,
                        text_color=color,
                    )
        except Exception:
            pass

    # ── Video generation ──────────────────────────────────────

    def _generate(self):
        prompt = self._prompt_box.get("1.0", "end-1c").strip()
        if not prompt:
            self._log("Please enter a prompt first.")
            return

        from modules.comfyui import is_comfyui_running, generate_video
        if not is_comfyui_running():
            self._log(
                "⚠️  ComfyUI is not running.\n"
                "Start it with:  python ~/ComfyUI/main.py"
            )
            return

        self._log(f"🎬 Generating: {prompt}")
        generate_video(
            prompt=prompt,
            on_result=lambda r: self.after(0, lambda: self._log(r)),
            on_error=lambda e: self.after(0, lambda: self._log(f"❌ {e}")),
        )

    # ── Helpers ──────────────────────────────────────────────

    def _section(self, parent, title: str):
        T = self.theme
        ctk.CTkLabel(
            parent,
            text=title,
            font=("Arial", 13, "bold"),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=24, pady=(14, 4))

    def _card(self, parent) -> ctk.CTkFrame:
        T    = self.theme
        card = ctk.CTkFrame(
            parent, corner_radius=12, fg_color=T["bg_card"])
        card.pack(fill="x", padx=20, pady=(0, 4))
        return card

    def _row(self, parent, label: str, desc: str = "") -> ctk.CTkFrame:
        T   = self.theme
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=9)
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            left,
            text=label,
            font=("Arial", 14),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(anchor="w")
        if desc:
            ctk.CTkLabel(
                left,
                text=desc,
                font=("Arial", 11),
                text_color=T["text_secondary"],
                anchor="w",
                wraplength=560,
            ).pack(anchor="w")
        return row
