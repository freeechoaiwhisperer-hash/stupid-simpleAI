# ============================================================
#  FreedomForge AI — ui/models_tab.py
#  Model browser — curated list + live HuggingFace search
# ============================================================

import os
import queue
import shutil
import threading
from tkinter import filedialog

import customtkinter as ctk
import requests

from core import model_manager
from assets.i18n import t

MODELS_DIR = "./models"

CURATED = [
    {
        "name":     "TinyLlama 1.1B",
        "badge":    "⚡ Best for low-end PCs",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "670 MB", "ram": "2 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Tiny but surprisingly capable. Runs on almost anything. Perfect starting point.",
    },
    {
        "name":     "Phi-2 2.7B",
        "badge":    "🧠 Smart and compact",
        "filename": "phi-2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "coding", "chat"],
        "desc": "Microsoft's compact powerhouse. Excellent at reasoning, coding, and writing.",
    },
    {
        "name":     "Llama 3.2 3B",
        "badge":    "🦙 Latest from Meta",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "2.0 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Meta's latest compact model. Fast, capable, and fully open source.",
    },
    {
        "name":     "Mistral 7B Instruct",
        "badge":    "⚖️ Best all-rounder",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "The gold standard for local AI. Excellent at everything.",
    },
    {
        "name":     "Dolphin Mistral 7B",
        "badge":    "🐬 Uncensored",
        "filename": "dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/dolphin-2.2.1-mistral-7B-GGUF/resolve/main/dolphin-2.2.1-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["uncensored", "chat", "large"],
        "desc": "Mistral fine-tuned to never refuse. Loyal, direct, completely open.",
    },
    {
        "name":     "Dolphin Llama 3 8B",
        "badge":    "🐬 Uncensored + Powerful",
        "filename": "dolphin-2.9-llama3-8b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/dolphin-2.9-llama3-8b-GGUF/resolve/main/dolphin-2.9-llama3-8b-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["uncensored", "chat", "large"],
        "desc": "Dolphin on Llama 3. Powerful, uncensored, deeply loyal.",
    },
    {
        "name":     "Llama 3.1 8B Instruct",
        "badge":    "🦙 Most powerful",
        "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
        "size": "4.9 GB", "ram": "10 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Meta's flagship open source model. State of the art.",
    },
    {
        "name":     "CodeLlama 7B",
        "badge":    "💻 Coding specialist",
        "filename": "codellama-7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "Fine-tuned specifically for code. Write, debug, and explain in any language.",
    },
    {
        "name":     "DeepSeek Coder 6.7B",
        "badge":    "💻 Best code model",
        "filename": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/deepseek-coder-6.7B-instruct-GGUF/resolve/main/deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "size": "3.8 GB", "ram": "8 GB+",
        "tags": ["coding", "large"],
        "desc": "DeepSeek's dedicated coding model. Exceptional at writing and reviewing code.",
    },
    {
        "name":     "Gemma 2 2B",
        "badge":    "🔵 Google",
        "filename": "gemma-2-2b-it-Q4_K_M.gguf",
        "url":      "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf",
        "size": "1.6 GB", "ram": "4 GB+",
        "tags": ["popular", "small", "chat"],
        "desc": "Google's compact instruction model. Clean, fast, and capable.",
    },
    {
        "name":     "Qwen2.5 7B",
        "badge":    "🌏 Multilingual",
        "filename": "qwen2.5-7b-instruct-q4_k_m.gguf",
        "url":      "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "size": "4.7 GB", "ram": "8 GB+",
        "tags": ["multilingual", "chat", "large"],
        "desc": "Alibaba's multilingual powerhouse. English, Chinese, and many others.",
    },
    {
        "name":     "OpenHermes 2.5 Mistral",
        "badge":    "🧙 Smart assistant",
        "filename": "openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf",
        "size": "4.1 GB", "ram": "8 GB+",
        "tags": ["popular", "chat", "large"],
        "desc": "Mistral fine-tuned on high quality instructions. Sharp and reliable.",
    },
    {
        "name":     "Mixtral 8x7B",
        "badge":    "🚀 Mixture of experts",
        "filename": "mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "url":      "https://huggingface.co/TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF/resolve/main/mixtral-8x7b-instruct-v0.1.Q3_K_M.gguf",
        "size": "19 GB", "ram": "24 GB+",
        "tags": ["popular", "large", "chat"],
        "desc": "Mistral's mixture-of-experts. GPT-4 level. Needs a powerful machine.",
    },
    {
        "name":     "Llava 1.6 Mistral 7B",
        "badge":    "👁️ Can see images",
        "filename": "llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "url":      "https://huggingface.co/cjpais/llava-1.6-mistral-7b-gguf/resolve/main/llava-v1.6-mistral-7b.Q4_K_M.gguf",
        "size": "4.4 GB", "ram": "8 GB+",
        "tags": ["vision", "large"],
        "desc": "Multimodal — can see and describe images. Show it a photo and ask questions.",
    },
]

FILTER_TAGS = [
    "all", "popular", "small", "large",
    "coding", "uncensored", "vision", "multilingual", "chat"
]


class ModelsPanel(ctk.CTkFrame):

    def __init__(self, master, app, theme: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app         = app
        self.theme       = theme
        self._active_tag = "all"
        self._hf_loading = False
        self._build()

    def apply_theme(self, theme: dict):
        self.theme = theme
        self._rebuild()

    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        T = self.theme

        # Header
        hdr = ctk.CTkFrame(
            self, fg_color="transparent", height=56)
        hdr.pack(fill="x", padx=22, pady=(20, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr,
            text=f"📦  {t('models_title')}",
            font=("Arial", 22, "bold"),
            text_color=T["text_primary"],
        ).pack(side="left", anchor="w")

        ctk.CTkLabel(
            hdr,
            text=t("models_subtitle"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=16, anchor="w")

        # Sub-tabs
        tab_bar = ctk.CTkFrame(
            self, fg_color=T["bg_topbar"], height=46)
        tab_bar.pack(fill="x", pady=(10, 0))
        tab_bar.pack_propagate(False)

        self._tab_btns = {}
        for label, key in [
            (t("models_curated"),   "curated"),
            (t("models_search_hf"), "search"),
        ]:
            b = ctk.CTkButton(
                tab_bar, text=label,
                font=("Arial", 13), height=46,
                corner_radius=0,
                fg_color="transparent",
                hover_color=T["bg_hover"],
                text_color=T["text_secondary"],
                command=lambda k=key: self._switch_tab(k))
            b.pack(side="left")
            self._tab_btns[key] = b

        self._content = ctk.CTkFrame(
            self, fg_color="transparent")
        self._content.pack(fill="both", expand=True)

        self._switch_tab("curated")

    def _switch_tab(self, key: str):
        T = self.theme
        for k, b in self._tab_btns.items():
            b.configure(
                fg_color=T["bg_hover"] if k == key else "transparent",
                text_color=T["text_primary"] if k == key else T["text_secondary"],
                font=("Arial", 13, "bold") if k == key else ("Arial", 13),
            )
        for w in self._content.winfo_children():
            w.destroy()
        if key == "curated":
            self._build_curated()
        else:
            self._build_search()

    # ── Curated ──────────────────────────────────────────────

    def _build_curated(self):
        T = self.theme

        # Filter bar
        fbar = ctk.CTkFrame(
            self._content, fg_color="transparent", height=50)
        fbar.pack(fill="x", padx=16, pady=(10, 4))
        fbar.pack_propagate(False)

        ctk.CTkLabel(
            fbar, text=t("models_filter"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=(4, 8))

        self._filter_btns = {}
        for tag in FILTER_TAGS:
            label = t(f"filter_{tag}", )
            b = ctk.CTkButton(
                fbar, text=label,
                width=86, height=28,
                corner_radius=14,
                font=("Arial", 11),
                fg_color=T["accent"] if tag == self._active_tag else T["bg_card"],
                hover_color=T["accent_hover"] if tag == self._active_tag else T["bg_hover"],
                text_color="#ffffff" if tag == self._active_tag else T["text_secondary"],
                command=lambda tg=tag: self._filter(tg),
            )
            b.pack(side="left", padx=3)
            self._filter_btns[tag] = b

        # Model list
        self._model_scroll = ctk.CTkScrollableFrame(
            self._content, fg_color="transparent")
        self._model_scroll.pack(
            fill="both", expand=True, padx=12, pady=(4, 0))

        # Bottom buttons
        bot = ctk.CTkFrame(
            self._content, fg_color="transparent", height=54)
        bot.pack(fill="x", padx=16, pady=(4, 10))
        bot.pack_propagate(False)

        for label, cmd in [
            (t("models_paste_url"), self._add_url),
            (t("models_add_local"), self._add_local),
        ]:
            ctk.CTkButton(
                bot, text=label, width=186, height=38,
                corner_radius=8,
                fg_color=T["bg_card"],
                hover_color=T["bg_hover"],
                text_color=T["text_secondary"],
                font=("Arial", 12),
                command=cmd,
            ).pack(side="left", padx=4)

        self._render_curated()

    def _render_curated(self):
        T = self.theme
        for w in self._model_scroll.winfo_children():
            w.destroy()

        tag    = self._active_tag
        models = [m for m in CURATED
                  if tag == "all" or tag in m.get("tags", [])]

        if not models:
            ctk.CTkLabel(
                self._model_scroll,
                text="No models in this category.",
                font=("Arial", 13),
                text_color=T["text_secondary"],
            ).pack(pady=40)
            return

        for m in models:
            self._model_row(self._model_scroll, m)

    def _model_row(self, parent, m: dict):
        T      = self.theme
        have   = os.path.exists(os.path.join(MODELS_DIR, m["filename"]))
        loaded = (model_manager.get_current_model() == m["filename"])

        row = ctk.CTkFrame(parent, corner_radius=12,
                           fg_color=T["bg_card"])
        row.pack(fill="x", pady=5, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both",
                  expand=True, padx=14, pady=12)

        # Title row
        tr = ctk.CTkFrame(info, fg_color="transparent")
        tr.pack(anchor="w", fill="x")

        ctk.CTkLabel(
            tr, text=m["name"],
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            tr, text=f"  {m['badge']}",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(side="left")

        if loaded:
            ctk.CTkLabel(tr, text=f"  {t('models_active')}",
                         font=("Arial", 11, "bold"),
                         text_color=T["gold"]).pack(side="left")
        elif have:
            ctk.CTkLabel(tr, text=f"  {t('models_downloaded')}",
                         font=("Arial", 11),
                         text_color=T["green"]).pack(side="left")

        # Description
        ctk.CTkLabel(
            info, text=m["desc"],
            font=("Arial", 11),
            text_color=T["text_secondary"],
            anchor="w", wraplength=580, justify="left",
        ).pack(anchor="w", pady=(2, 0))

        # Meta tags
        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(anchor="w", pady=(5, 0))

        for label, val in [("Size", m["size"]), ("RAM", m["ram"])]:
            ctk.CTkLabel(
                meta,
                text=f"{label}: {val}",
                font=("Arial", 10),
                text_color=T["text_dim"],
                fg_color=T["bg_hover"],
                corner_radius=4,
                width=110,
            ).pack(side="left", padx=(0, 6))

        # Button
        btn_frame = ctk.CTkFrame(
            row, fg_color="transparent", width=124)
        btn_frame.pack(side="right", padx=12, pady=12)
        btn_frame.pack_propagate(False)

        if loaded:
            ctk.CTkLabel(
                btn_frame, text=t("models_running"),
                font=("Arial", 12, "bold"),
                text_color=T["gold"],
            ).pack(expand=True)
        elif have:
            ctk.CTkButton(
                btn_frame, text=t("models_load"),
                height=36, corner_radius=8,
                fg_color="#1a4a1a", hover_color="#0d2e0d",
                text_color="#ffffff",
                command=lambda fn=m["filename"]: self._load(fn),
            ).pack(fill="x", pady=(0, 4))
            ctk.CTkButton(
                btn_frame, text=t("models_delete"),
                height=22, corner_radius=6,
                fg_color="#2a1212", hover_color="#3a1a1a",
                text_color=T["text_secondary"],
                font=("Arial", 10),
                command=lambda fn=m["filename"]: self._delete(fn),
            ).pack(fill="x")
        else:
            ctk.CTkButton(
                btn_frame, text=t("models_download"),
                height=36, corner_radius=8,
                fg_color=T["accent"], hover_color=T["accent_hover"],
                text_color="#ffffff",
                command=lambda mo=m: self._download(mo),
            ).pack(fill="x")

    def _filter(self, tag: str):
        T = self.theme
        self._active_tag = tag
        for tg, b in self._filter_btns.items():
            active = tg == tag
            b.configure(
                fg_color=T["accent"] if active else T["bg_card"],
                hover_color=T["accent_hover"] if active else T["bg_hover"],
                text_color="#ffffff" if active else T["text_secondary"],
            )
        self._render_curated()

    # ── HuggingFace search ───────────────────────────────────

    def _build_search(self):
        T = self.theme

        # Search bar
        sbar = ctk.CTkFrame(
            self._content, fg_color="transparent", height=58)
        sbar.pack(fill="x", padx=16, pady=(14, 4))
        sbar.pack_propagate(False)

        self._search_entry = ctk.CTkEntry(
            sbar,
            placeholder_text="Search HuggingFace for any GGUF model…",
            font=("Arial", 13), height=44,
            fg_color=T["bg_input"],
            text_color=T["text_primary"],
            border_color=T["border"],
            placeholder_text_color=T["text_secondary"],
        )
        self._search_entry.pack(
            side="left", fill="both", expand=True, padx=(0, 8))
        self._search_entry.bind(
            "<Return>", lambda _: self._hf_search())

        ctk.CTkButton(
            sbar, text="Search",
            width=106, height=44,
            corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            text_color="#ffffff",
            font=("Arial", 13, "bold"),
            command=self._hf_search,
        ).pack(side="right")

        ctk.CTkLabel(
            self._content,
            text="Millions of open source GGUF models available on HuggingFace.",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(0, 6))

        # Quick searches
        quick = ctk.CTkFrame(
            self._content, fg_color="transparent", height=38)
        quick.pack(fill="x", padx=16, pady=(0, 8))
        quick.pack_propagate(False)

        ctk.CTkLabel(
            quick, text="Quick:",
            font=("Arial", 11),
            text_color=T["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        for term in ["dolphin", "llama", "mistral", "deepseek",
                     "codellama", "qwen", "gemma", "phi", "wizard"]:
            ctk.CTkButton(
                quick, text=term,
                width=82, height=26,
                corner_radius=13,
                font=("Arial", 11),
                fg_color=T["bg_card"],
                hover_color=T["bg_hover"],
                text_color=T["text_secondary"],
                command=lambda term=term: self._quick_search(term),
            ).pack(side="left", padx=3)

        # Results
        self._hf_scroll = ctk.CTkScrollableFrame(
            self._content, fg_color="transparent")
        self._hf_scroll.pack(
            fill="both", expand=True, padx=12, pady=4)

        ctk.CTkLabel(
            self._hf_scroll,
            text="Type a model name and press Search.",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        ).pack(pady=60)

    def _quick_search(self, term: str):
        try:
            self._search_entry.delete(0, "end")
            self._search_entry.insert(0, term)
        except Exception:
            pass
        self._hf_search()

    def _hf_search(self):
        if self._hf_loading:
            return
        T = self.theme
        try:
            query = self._search_entry.get().strip()
        except Exception:
            return
        if not query:
            return

        self._hf_loading = True
        for w in self._hf_scroll.winfo_children():
            w.destroy()

        status = ctk.CTkLabel(
            self._hf_scroll,
            text=f"🔍  {t('models_searching')} \"{query}\"…",
            font=("Arial", 13),
            text_color=T["text_secondary"],
        )
        status.pack(pady=60)

        def _search():
            try:
                url = (
                    f"https://huggingface.co/api/models"
                    f"?search={query}&filter=gguf"
                    f"&sort=downloads&limit=24&full=false"
                )
                r = requests.get(url, timeout=12)
                r.raise_for_status()
                results = r.json()
                self.after(0, lambda: self._render_hf(results, query))
            except Exception as e:
                self.after(0, lambda: self._hf_error(str(e)))
            finally:
                self._hf_loading = False

        threading.Thread(target=_search, daemon=True).start()

    def _render_hf(self, results: list, query: str):
        T = self.theme
        for w in self._hf_scroll.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(
                self._hf_scroll,
                text=f"{t('models_no_results')} \"{query}\".",
                font=("Arial", 13),
                text_color=T["text_secondary"],
            ).pack(pady=40)
            return

        ctk.CTkLabel(
            self._hf_scroll,
            text=f"{len(results)} {t('models_found')}",
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(anchor="w", pady=(0, 8))

        for model in results:
            self._hf_row(self._hf_scroll, model)

    def _hf_row(self, parent, model: dict):
        T         = self.theme
        model_id  = model.get("modelId", model.get("id", "Unknown"))
        downloads = model.get("downloads", 0)
        likes     = model.get("likes", 0)

        row = ctk.CTkFrame(parent, corner_radius=10,
                           fg_color=T["bg_card"])
        row.pack(fill="x", pady=4, padx=4)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both",
                  expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=model_id,
            font=("Arial", 13, "bold"),
            text_color=T["text_primary"],
            anchor="w",
        ).pack(anchor="w")

        meta = ctk.CTkFrame(info, fg_color="transparent")
        meta.pack(anchor="w", pady=(2, 0))

        if downloads:
            ctk.CTkLabel(
                meta, text=f"⬇ {downloads:,}",
                font=("Arial", 10),
                text_color=T["text_secondary"],
            ).pack(side="left", padx=(0, 10))
        if likes:
            ctk.CTkLabel(
                meta, text=f"❤ {likes:,}",
                font=("Arial", 10),
                text_color=T["text_secondary"],
            ).pack(side="left")

        ctk.CTkButton(
            row, text=t("models_view_files"),
            width=116, height=34,
            corner_radius=8,
            fg_color=T["accent"], hover_color=T["accent_hover"],
            text_color="#ffffff",
            command=lambda mid=model_id: self._show_files(mid),
        ).pack(side="right", padx=12, pady=10)

    def _show_files(self, model_id: str):
        T   = self.theme
        win = ctk.CTkToplevel(self)
        win.title(model_id)
        win.geometry("720x520")
        win.configure(fg_color=T["bg_panel"])
        win.grab_set()

        ctk.CTkLabel(
            win, text=model_id,
            font=("Arial", 15, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(18, 2), padx=22, anchor="w")

        ctk.CTkLabel(
            win,
            text=t("models_select_dl"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        ).pack(padx=22, anchor="w")

        status = ctk.CTkLabel(
            win, text=t("models_loading_files"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        )
        status.pack(pady=20)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        def _fetch():
            try:
                r    = requests.get(
                    f"https://huggingface.co/api/models/{model_id}",
                    timeout=12)
                r.raise_for_status()
                data  = r.json()
                files = [
                    s for s in data.get("siblings", [])
                    if s.get("rfilename", "").endswith(".gguf")
                ]
                win.after(0, lambda: _show(files))
            except Exception as e:
                win.after(0, lambda: status.configure(
                    text=f"❌  {e}",
                    text_color=T["text_error"]))

        def _show(files: list):
            try:
                status.destroy()
            except Exception:
                pass

            if not files:
                ctk.CTkLabel(
                    scroll,
                    text=t("models_no_files"),
                    text_color=T["text_secondary"],
                ).pack(pady=20)
                return

            for f in files:
                fname    = f.get("rfilename", "")
                size_b   = f.get("size", 0)
                size_str = (
                    f"{size_b/(1024**3):.1f} GB"
                    if size_b > 1024**3
                    else f"{size_b/(1024**2):.0f} MB"
                    if size_b else "?"
                )
                frow = ctk.CTkFrame(
                    scroll, corner_radius=8, fg_color=T["bg_card"])
                frow.pack(fill="x", pady=4, padx=2)

                fi = ctk.CTkFrame(frow, fg_color="transparent")
                fi.pack(side="left", fill="both",
                        expand=True, padx=12, pady=8)

                ctk.CTkLabel(
                    fi, text=fname,
                    font=("Arial", 12, "bold"),
                    text_color=T["text_primary"],
                    anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    fi, text=size_str,
                    font=("Arial", 10),
                    text_color=T["text_secondary"],
                    anchor="w",
                ).pack(anchor="w")

                dl_url = (
                    f"https://huggingface.co/{model_id}"
                    f"/resolve/main/{fname}"
                )
                have = os.path.exists(os.path.join(MODELS_DIR, fname))

                if have:
                    ctk.CTkLabel(
                        frow,
                        text=t("models_downloaded"),
                        font=("Arial", 11),
                        text_color=T["green"],
                    ).pack(side="right", padx=12, pady=10)
                else:
                    ctk.CTkButton(
                        frow, text=t("models_download"),
                        width=116, height=32,
                        corner_radius=8,
                        fg_color=T["accent"],
                        hover_color=T["accent_hover"],
                        text_color="#ffffff",
                        command=lambda u=dl_url, fn=fname: (
                            win.destroy(),
                            self._download({
                                "name":     fn,
                                "filename": fn,
                                "url":      u,
                                "size":     size_str,
                                "ram":      "?",
                                "desc":     f"From {model_id}",
                            })
                        ),
                    ).pack(side="right", padx=12, pady=8)

        threading.Thread(target=_fetch, daemon=True).start()

    def _hf_error(self, msg: str):
        T = self.theme
        for w in self._hf_scroll.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._hf_scroll,
            text=f"❌  Search failed: {msg}\n\nCheck your internet connection.",
            font=("Arial", 13),
            text_color=T["text_error"],
        ).pack(pady=40)

    # ── Actions ──────────────────────────────────────────────

    def _load(self, filename: str):
        self.app.load_model(filename)
        self.app.switch_panel("Chat")

    def _delete(self, filename: str):
        path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
        self.refresh()

    def _download(self, model: dict):
        DownloadWindow(self, model, self.theme, self.refresh)

    def _add_url(self):
        dlg = ctk.CTkInputDialog(
            text=t("models_url_dialog"),
            title="Add Model by URL")
        url = dlg.get_input()
        if url and url.strip():
            filename = os.path.basename(
                url.strip()).split("?")[0]
            if not filename.endswith(".gguf"):
                filename += ".gguf"
            self._download({
                "name": filename, "filename": filename,
                "url": url.strip(), "size": "?",
                "ram": "?", "desc": "Custom URL",
            })

    def _add_local(self):
        path = filedialog.askopenfilename(
            title=t("models_select_file"),
            filetypes=[("GGUF files", "*.gguf"),
                       ("All files", "*.*")])
        if path:
            os.makedirs(MODELS_DIR, exist_ok=True)
            dest = os.path.join(MODELS_DIR, os.path.basename(path))
            shutil.copy2(path, dest)
            self.refresh()
            try:
                self.app.chat_panel.sys_message(
                    f"✅  {t('models_added')} {os.path.basename(path)}")
            except Exception:
                pass

    def refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Download window ──────────────────────────────────────────

class DownloadWindow(ctk.CTkToplevel):
    """
    Pop-up that downloads a model file with:
    • A progress bar (0 → 100 %)
    • Live speed (MB/s) and estimated time remaining
    • A user-friendly error dialog with Retry / Cancel on failure
    • Automatic clean-up of partial files if the download fails
    • Auto-refreshes the parent model list on success
    """

    def __init__(self, parent, model: dict,
                 theme: dict, on_done=None):
        super().__init__(parent)
        self._parent  = parent
        self.on_done  = on_done
        self._q       = queue.Queue()
        self._model   = model
        self._theme   = theme
        T             = theme

        self.title("Downloading")
        self.geometry("560x230")
        self.resizable(False, False)
        self.configure(fg_color=T["bg_panel"])
        self.grab_set()

        # Title
        ctk.CTkLabel(
            self,
            text=f"⬇  {model.get('name', model['filename'])}",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(22, 4))

        # Progress bar
        self.bar = ctk.CTkProgressBar(
            self, width=500,
            progress_color=T["accent"],
            fg_color=T["bg_card"],
        )
        self.bar.set(0)
        self.bar.pack(pady=(8, 4))

        # Primary status line: "X MB / Y MB  (Z%)"
        self.lbl = ctk.CTkLabel(
            self,
            text=t("models_connecting"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        )
        self.lbl.pack()

        # Secondary line: speed + ETA
        self.eta_lbl = ctk.CTkLabel(
            self, text="",
            font=("Arial", 11),
            text_color=T["text_dim"],
        )
        self.eta_lbl.pack(pady=(2, 0))

        ctk.CTkLabel(
            self,
            text=t("models_minimize"),
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(pady=(6, 0))

        threading.Thread(
            target=self._dl, args=(model,), daemon=True).start()
        self._poll()

    # ── Download thread ──────────────────────────────────────

    def _dl(self, model: dict):
        dest = os.path.join(MODELS_DIR, model["filename"])
        try:
            os.makedirs(MODELS_DIR, exist_ok=True)
            r = requests.get(
                model["url"], stream=True, timeout=60)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        self._q.put(("p", done / total, done, total))
            self._q.put(("done", None))
        except Exception as e:
            # Clean up any partial file so it doesn't appear as downloaded
            try:
                if os.path.exists(dest):
                    os.remove(dest)
            except OSError:
                pass
            self._q.put(("error", str(e)))

    # ── UI polling ───────────────────────────────────────────

    def _poll(self):
        import time
        # Lazily initialise speed tracking on first call
        if not hasattr(self, "_dl_start"):
            self._dl_start   = time.monotonic()
            self._last_bytes = 0
            self._last_ts    = self._dl_start

        try:
            while True:
                msg = self._q.get_nowait()
                if msg[0] == "p":
                    _, pct, done, total = msg
                    now = time.monotonic()

                    # Update progress bar
                    self.bar.set(pct)

                    # Speed over the last interval
                    interval = now - self._last_ts
                    if interval > 0:
                        speed = (done - self._last_bytes) / interval  # bytes/s
                    else:
                        speed = 0
                    self._last_bytes = done
                    self._last_ts    = now

                    # Elapsed / ETA
                    elapsed  = now - self._dl_start
                    avg_speed = done / elapsed if elapsed > 0 else 0
                    remaining = total - done
                    eta_sec   = remaining / avg_speed if avg_speed > 0 else 0

                    # Format sizes
                    done_mb  = done  / (1024 ** 2)
                    total_mb = total / (1024 ** 2)
                    spd_mb   = speed / (1024 ** 2)

                    # ETA string
                    if eta_sec > 0 and avg_speed > 0:
                        if eta_sec < 60:
                            eta_str = f"{eta_sec:.0f}s remaining"
                        elif eta_sec < 3600:
                            eta_str = f"{eta_sec/60:.0f}m remaining"
                        else:
                            eta_str = f"{eta_sec/3600:.1f}h remaining"
                    else:
                        eta_str = "calculating…"

                    self.lbl.configure(
                        text=f"{done_mb:.1f} MB / {total_mb:.1f} MB"
                             f"  ({pct * 100:.1f}%)"
                    )
                    self.eta_lbl.configure(
                        text=f"{spd_mb:.2f} MB/s  •  {eta_str}"
                    )

                elif msg[0] == "done":
                    self.bar.set(1.0)
                    self.lbl.configure(text=t("models_complete"))
                    self.eta_lbl.configure(text="")
                    self.after(1400, self._finish)
                    return

                elif msg[0] == "error":
                    self._show_error(msg[1])
                    return

        except queue.Empty:
            pass
        self.after(110, self._poll)

    # ── Error dialog ─────────────────────────────────────────

    def _show_error(self, message: str):
        """Replace window contents with a user-friendly error + retry button."""
        T = self._theme

        # Clear everything and rebuild
        for w in self.winfo_children():
            w.destroy()

        self.geometry("540x240")

        ctk.CTkLabel(
            self, text="⚠️  Download Failed",
            font=("Arial", 15, "bold"),
            text_color=T.get("yellow", "#ffaa00"),
        ).pack(pady=(26, 6))

        # Show a short, readable error (not a raw Python traceback)
        short = message[:120] + "…" if len(message) > 120 else message
        ctk.CTkLabel(
            self, text=short,
            font=("Arial", 11),
            text_color=T["text_secondary"],
            wraplength=480, justify="center",
        ).pack(padx=24)

        ctk.CTkLabel(
            self,
            text="The partial file has been removed.\n"
                 "Check your internet connection and try again.",
            font=("Arial", 11),
            text_color=T["text_dim"],
            justify="center",
        ).pack(pady=(8, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)

        ctk.CTkButton(
            btn_row, text="🔄  Retry",
            width=130, height=36,
            corner_radius=8,
            fg_color=T["accent"],
            hover_color=T["accent_hover"],
            text_color="#ffffff",
            command=self._retry,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row, text="Cancel",
            width=100, height=36,
            corner_radius=8,
            fg_color=T["bg_hover"],
            hover_color=T["bg_card"],
            text_color=T["text_secondary"],
            command=self.destroy,
        ).pack(side="left", padx=8)

    def _retry(self):
        """Reset state and restart the download."""
        # Remove partial attributes so _poll reinitialises timers
        for attr in ("_dl_start", "_last_bytes", "_last_ts"):
            try:
                delattr(self, attr)
            except AttributeError:
                pass

        # Clear error UI and rebuild original layout
        for w in self.winfo_children():
            w.destroy()

        T = self._theme
        self.geometry("560x230")
        self._q = queue.Queue()

        ctk.CTkLabel(
            self,
            text=f"⬇  {self._model.get('name', self._model['filename'])}",
            font=("Arial", 14, "bold"),
            text_color=T["text_primary"],
        ).pack(pady=(22, 4))

        self.bar = ctk.CTkProgressBar(
            self, width=500,
            progress_color=T["accent"],
            fg_color=T["bg_card"],
        )
        self.bar.set(0)
        self.bar.pack(pady=(8, 4))

        self.lbl = ctk.CTkLabel(
            self,
            text=t("models_connecting"),
            font=("Arial", 12),
            text_color=T["text_secondary"],
        )
        self.lbl.pack()

        self.eta_lbl = ctk.CTkLabel(
            self, text="",
            font=("Arial", 11),
            text_color=T["text_dim"],
        )
        self.eta_lbl.pack(pady=(2, 0))

        ctk.CTkLabel(
            self,
            text=t("models_minimize"),
            font=("Arial", 10),
            text_color=T["text_dim"],
        ).pack(pady=(6, 0))

        threading.Thread(
            target=self._dl, args=(self._model,), daemon=True).start()
        self._poll()

    # ── Completion ───────────────────────────────────────────

    def _finish(self):
        # Auto-refresh model list in the parent panel
        if self.on_done:
            self.on_done()
        try:
            self.destroy()
        except Exception:
            pass

