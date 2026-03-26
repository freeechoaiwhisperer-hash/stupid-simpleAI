# ============================================================
#  FreedomForge AI — ui/components/toolbar.py
#  Top toolbar widget
# ============================================================

from __future__ import annotations

import customtkinter as ctk
from typing import Callable


class Toolbar(ctk.CTkFrame):
    """Application top toolbar with title and action buttons."""

    def __init__(self, parent, title: str = "FreedomForge AI", theme: dict | None = None, **kwargs):
        """
        Args:
            parent: Parent widget.
            title: Application title to display.
            theme: Optional theme dict for colors.
        """
        super().__init__(parent, **kwargs)
        self.theme = theme or {}
        self._build(title)

    def _build(self, title: str) -> None:
        bg = self.theme.get("bg_topbar", "#080808")
        fg = self.theme.get("text_primary", "#dddddd")
        self.configure(fg_color=bg)

        self.title_label = ctk.CTkLabel(self, text=title, text_color=fg, font=("", 16, "bold"))
        self.title_label.pack(side="left", padx=16, pady=8)

    def add_button(self, text: str, command: Callable, side: str = "right") -> ctk.CTkButton:
        """Add an action button to the toolbar."""
        btn = ctk.CTkButton(self, text=text, command=command, width=80)
        btn.pack(side=side, padx=6, pady=4)
        return btn
