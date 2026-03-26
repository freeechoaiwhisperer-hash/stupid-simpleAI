# ============================================================
#  FreedomForge AI — ui/wizard.py
#  First run setup wizard
# ============================================================

import os
import queue
import random
import shutil
import threading
from tkinter import filedialog

import customtkinter as ctk
import requests

from core import hardware
from core.model_manager import MODELS_DIR
from assets.i18n import t
from assets.themes import get as get_theme
from ui.models_tab import CURATED

MIRANDA_QUOTES = [
    "✨ \"It does not do to dwell on dreams and forget to live.\"",
    "🪄 \"It takes a great deal of bravery to stand up to our enemies,\nbut even more to stand up to our friends.\"",
    "💫 \"Happiness can be found even in the darkest of times,\nif one only remembers to turn on the light.\"",
    "⚡ \"Do what is right, not what is easy.\"",
    "🌟 \"It is our choices that show what we truly are,\nfar more than our abilities.\"",
    "🪄 Why did the AI cross the road?\nTo get to the other dataset! 😄",
    "✨ What do you call an AI that sings?\nAlgo-rhythmic! 🎵",
    "🌙 \"Not all those who wander are lost.\"",
    "⭐ \"Every moment is a fresh beginning.\"",
]

WAND_FRAMES = [
    "🪄         ", "  ✨       ", "    ✨     ",
    "      ✨   ", "    ✨     ", "  ✨       ",
]


class SetupWizard(ctk.CTkToplevel):

    def __init__(self, parent, on_complete, theme_name="Midnight"):
        super().__init__(parent)
        self.parent      = parent
        self.on_complete = on_complete
        self._q          = queue.Queue()
        self._wand_alive = True
        self._wand_idx   = 0

        T = get_theme(theme_name)
        self.theme = T

        self.title(t("wizard_title"))
        self.geometry("700x560")
        self.resizable(False, False)
        self.configure(fg_color=T["bg_panel"])
        self.protocol("WM_DELETE_WINDOW", self._abort)

        self.container = ctk.CTkFrame(
            self, fg_color="transparent")
        self.container.pack(
            fill="both", expand=True, padx=34, pady=26)

        self._show_welcome()

    def _abort(self):
        self._wand_alive = False
        self.parent.destroy()

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    # ── Wand ─────────────────────────────────────────────────

    def _wand_tick(self, label):
        if not self._wand_alive:
            return
        try:
            self._wand_idx = (self._wand_idx + 1) % len(WAND_FRAMES)
            label.configure(text=WAND_FRAMES[self._wand_idx])
            self.after(130, lambda: self._wand_tick(label))
        except Exception:
            pass

    def _make_wand(self, size=44):
        T   = self.theme
        lbl = ctk.CTkLabel(
            self.container,
            text=WAND_FRAMES[0],
            font=("Arial", size),
            text_color=T["purple"],
        )
        lbl.pack(pady=(4, 0))
        self._wand_tick(lbl)
        return lbl

    # ── Screen 1: Welcome ────────────────────────────────────

    def _show_welcome(self):
        self._clear()
        T = self.theme

        self._make_wand(48)

        ctk.CTkLabel(
            self.container,
            text=t("wizard_welcome"),
            font=("Arial", 26, "bold"),
            text_color=T["gold"],
        ).pack(pady=(4, 0))

        ctk.CTkLabel(
            self.container,
            text=t("wizard_tagline"),
            font=("Arial", 13),
            text_color=T["text_secondary"],
        ).pack(pady=(0, 12))

        # System info card
        info    = hardware.get_system_info()
        ram     = info["ram_gb"]
        gpu     = info["gpu"]
        rec     = hardware.recommend_model(ram)
        rec_m   = next(
            (m for m in CURATED if m["filename"] == rec),
            CURATED[0])

        card = ctk.CTkFrame(
            self.container, corner_radius=12,
            fg_color=T["bg_card"])
        card.pack(fill="x", pady=10)

        ctk.CTkLabel(
            card,
            text=t("wizard_your_pc"),
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        gpu_str = (
            f"{gpu['name']}  ({gpu['vram_gb']} GB VRAM)  {t('wizard_gpu_yes')}"
            if gpu["available"]
            else t("wizard_gpu_no")
        )

        ctk.CTkLabel(
            card,
            text=f"{t('wizard_ram')} {ram} GB     GPU: {gpu_str}",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=16)

        ctk.CTkLabel(
            card,
            text=f"{t('wizard_rec')}  {rec_m['name']}  {rec_m['badge']}",
            font=("Arial", 12),
            text_color=T["green"],
        ).pack(anchor="w", padx=16, pady=(4, 12))

        # Miranda quote
        ctk.CTkLabel(
            self.container,
            text=random.choice(MIRANDA_QUOTES),
            font=("Arial", 11, "italic"),
            text_color="#554466",
            justify="center",
        ).pack(pady=(4, 14))

        ctk.CTkButton(
            self.container,
            text=t("wizard_lets_go"),
            width=300, height=54,
            corner_radius=27,
            font=("Arial", 15, "bold"),
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            text_color="#ffffff",
            command=self._show_options,
        ).pack(pady=6)

    # ── Screen 2: Options ────────────────────────────────────

    def _show_options(self):
        self._clear()
        T = self.theme

        ctk.CTkLabel(
            self.container,
            text=f"📦  {t('wizard_lib_title')}",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(8, 4), anchor="w")

        ctk.CTkLabel(
            self.container,
            text=t("wizard_how"),
            font=("Arial", 13),
            text_color=T["text_secondary"],
        ).pack(anchor="w", pady=(0, 16))

        rec   = hardware.recommend_model()
        rec_m = next(
            (m for m in CURATED if m["filename"] == rec),
            CURATED[0])

        opts = [
            (
                t("wizard_quick"),
                f"{t('wizard_quick_desc')} {rec_m['name']}  ({rec_m['size']})",
                T["accent"], T["accent_hover"],
                lambda: self._download_model(rec_m),
            ),
            (
                t("wizard_browse"),
                t("wizard_browse_desc"),
                "#1a4a2a", "#0d3020",
                self._show_browser,
            ),
            (
                t("wizard_local"),
                t("wizard_local_desc"),
                "#3a2a1a", "#261a0d",
                self._select_local,
            ),
        ]

        for title, desc, fg, hov, cmd in opts:
            ctk.CTkButton(
                self.container,
                text=f"{title}\n{desc}",
                width=600, height=72,
                corner_radius=12,
                font=("Arial", 13), anchor="w",
                fg_color=fg, hover_color=hov,
                text_color="#ffffff",
                command=cmd,
            ).pack(pady=6)

        # Unlock hint
        ctk.CTkFrame(
            self.container, height=1,
            fg_color=T["divider"],
        ).pack(fill="x", pady=16)

        hint_text = (
            f"{t('wizard_hint_title')}\n"
            f"{t('wizard_hint_body')}"
        )
        ctk.CTkLabel(
            self.container,
            text=hint_text,
            font=("Arial", 11),
            text_color=T["text_secondary"],
            justify="center",
        ).pack()

    # ── Screen 3: Browser ────────────────────────────────────

    def _show_browser(self):
        self._clear()
        T = self.theme

        ctk.CTkLabel(
            self.container,
            text=f"📚  {t('wizard_lib_title')}",
            font=("Arial", 20, "bold"),
            text_color=T["text_primary"],
        ).pack(anchor="w", pady=(4, 2))

        ctk.CTkLabel(
            self.container,
            text=t("wizard_lib_sub"),
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(
            self.container, height=360)
        scroll.pack(fill="x", pady=10)

        for m in CURATED:
            row = ctk.CTkFrame(
                scroll, corner_radius=10,
                fg_color=T["bg_card"])
            row.pack(fill="x", pady=4, padx=2)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both",
                      expand=True, padx=12, pady=8)

            ctk.CTkLabel(
                info,
                text=f"{m['name']}  {m['badge']}",
                font=("Arial", 12, "bold"),
                text_color=T["text_primary"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=f"{m['desc']}  •  {m['size']}  •  RAM: {m['ram']}",
                font=("Arial", 10),
                text_color=T["text_secondary"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkButton(
                row,
                text=t("models_download"),
                width=104, height=32,
                corner_radius=8,
                fg_color=T["accent"],
                hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda mo=m: self._download_model(mo),
            ).pack(side="right", padx=12, pady=8)

        ctk.CTkButton(
            self.container,
            text=t("wizard_back"),
            width=104, height=32,
            fg_color=T["bg_card"],
            hover_color=T["bg_hover"],
            text_color=T["text_secondary"],
            command=self._show_options,
        ).pack(pady=4)

    # ── Screen 4: Downloading ────────────────────────────────

    def _download_model(self, model: dict):
        self._clear()
        T = self.theme

        self._make_wand(36)

        ctk.CTkLabel(
            self.container,
            text=f"⬇  {t('wizard_dl_title')}",
            font=("Arial", 20, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(10, 4))

        ctk.CTkLabel(
            self.container,
            text=f"{model['name']}  •  {model['size']}",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        ).pack()

        bar = ctk.CTkProgressBar(
            self.container, width=520,
            progress_color=T["accent"],
            fg_color=T["bg_card"],
        )
        bar.set(0)
        bar.pack(pady=18)

        status = ctk.CTkLabel(
            self.container,
            text=t("wizard_starting"),
            font=("Arial", 13),
            text_color=T["text_primary"],
        )
        status.pack()

        ctk.CTkLabel(
            self.container,
            text=t("wizard_coffee"),
            font=("Arial", 11),
            text_color=T["text_secondary"],
            justify="center",
        ).pack(pady=10)

        ctk.CTkLabel(
            self.container,
            text=random.choice(MIRANDA_QUOTES),
            font=("Arial", 11, "italic"),
            text_color="#443344",
            justify="center",
        ).pack(pady=6)

        def _dl():
            try:
                os.makedirs(MODELS_DIR, exist_ok=True)
                r     = requests.get(
                    model["url"], stream=True, timeout=60)
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                done  = 0
                dest  = os.path.join(MODELS_DIR, model["filename"])
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            self._q.put(("p", done/total, done, total))
                self._q.put(("done", None))
            except Exception as e:
                self._q.put(("error", str(e)))

        threading.Thread(target=_dl, daemon=True).start()
        self._poll_dl(bar, status)

    def _poll_dl(self, bar, status):
        T = self.theme
        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == "p":
                    _, pct, done, total = msg
                    bar.set(pct)
                    status.configure(
                        text=f"{done/(1024**2):.0f} MB / "
                             f"{total/(1024**2):.0f} MB  "
                             f"({pct*100:.1f}%)"
                    )
                elif msg[0] == "done":
                    bar.set(1.0)
                    status.configure(text=t("wizard_done"))
                    self.after(1500, self._finish)
                    return
                elif msg[0] == "error":
                    status.configure(
                        text=f"❌  {msg[1]}",
                        text_color=T["text_error"])
                    self.after(3000, self._show_options)
                    return
        except queue.Empty:
            pass
        self.after(100, lambda: self._poll_dl(bar, status))

    def _select_local(self):
        path = filedialog.askopenfilename(
            title=t("models_select_file"),
            filetypes=[("GGUF files", "*.gguf"),
                       ("All files", "*.*")])
        if path:
            os.makedirs(MODELS_DIR, exist_ok=True)
            dest = os.path.join(MODELS_DIR, os.path.basename(path))
            shutil.copy2(path, dest)
            self._finish()

    def _finish(self):
        self._wand_alive = False
        self.destroy()
        self.on_complete()
