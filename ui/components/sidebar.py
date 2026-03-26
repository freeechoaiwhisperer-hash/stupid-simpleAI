# ============================================================
#  FreedomForge AI — ui/components/sidebar.py
#  Navigation sidebar widget
# ============================================================

from __future__ import annotations

import customtkinter as ctk
from typing import Callable


class Sidebar(ctk.CTkFrame):
    """Vertical navigation sidebar with icon buttons."""

    def __init__(self, parent, nav_items: list[tuple[str, str, str]], on_select: Callable[[str], None], theme: dict | None = None, **kwargs):
        """
        Args:
            parent: Parent widget.
            nav_items: List of (icon, label, key) tuples.
            on_select: Callback(key) called when item is clicked.
            theme: Optional theme dict for colors.
        """
        super().__init__(parent, **kwargs)
        self.theme = theme or {}
        self.on_select = on_select
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active_key: str | None = None

        self._build(nav_items)

    def _build(self, nav_items: list[tuple[str, str, str]]) -> None:
        bg = self.theme.get("bg_sidebar", "#0c0c0c")
        self.configure(fg_color=bg)

        for icon, label, key in nav_items:
            btn = ctk.CTkButton(
                self,
                text=f"{icon}  {label}",
                anchor="w",
                command=lambda k=key: self._handle_click(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._buttons[key] = btn

    def _handle_click(self, key: str) -> None:
        self.set_active(key)
        self.on_select(key)

    def set_active(self, key: str) -> None:
        """Highlight the active navigation item."""
        accent = self.theme.get("accent", "#1a5a9a")
        bg = self.theme.get("bg_sidebar", "#0c0c0c")

        for k, btn in self._buttons.items():
            btn.configure(fg_color=accent if k == key else bg)
        self._active_key = key
