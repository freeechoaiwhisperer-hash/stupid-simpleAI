# ============================================================
#  FreedomForge AI — ui/components/message_bubble.py
#  Reusable chat message bubble widget
# ============================================================

from __future__ import annotations

import customtkinter as ctk


class MessageBubble(ctk.CTkFrame):
    """A single chat message bubble (user or AI)."""

    def __init__(self, parent, text: str, role: str = "user", theme: dict | None = None, **kwargs):
        """
        Args:
            parent: Parent widget.
            text: Message text to display.
            role: "user", "ai", or "system".
            theme: Optional theme dict for colors.
        """
        super().__init__(parent, **kwargs)
        self.role = role
        self.theme = theme or {}

        self._build(text)

    def _build(self, text: str) -> None:
        fg = self.theme.get("text_you" if self.role == "user" else "text_ai", "#dddddd")
        bg = self.theme.get("bg_card", "#141414")
        self.configure(fg_color=bg)

        self.label = ctk.CTkLabel(
            self,
            text=text,
            wraplength=600,
            justify="left",
            text_color=fg,
            anchor="w",
        )
        self.label.pack(padx=10, pady=6, fill="x")

    def update_text(self, text: str) -> None:
        """Update the displayed message text (for streaming)."""
        self.label.configure(text=text)
