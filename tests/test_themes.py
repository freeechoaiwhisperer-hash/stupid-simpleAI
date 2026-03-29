"""Tests for assets/themes.py"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.themes import (
    THEMES,
    DEFAULT_THEME,
    get,
    names,
    display_names,
    name_from_display,
)


class TestThemesData:
    def test_themes_not_empty(self):
        assert len(THEMES) > 0

    def test_default_theme_exists(self):
        assert DEFAULT_THEME in THEMES

    def test_each_theme_has_required_keys(self):
        required_keys = {
            "display", "base", "bg_deep", "bg_panel", "accent",
            "text_primary", "text_error", "green", "red",
        }
        for name, theme in THEMES.items():
            missing = required_keys - set(theme.keys())
            assert not missing, f"Theme '{name}' missing keys: {missing}"

    def test_base_is_dark_or_light(self):
        for name, theme in THEMES.items():
            assert theme["base"] in ("dark", "light"), (
                f"Theme '{name}' has invalid base: {theme['base']}"
            )


class TestGet:
    def test_get_known_theme(self):
        result = get("Midnight")
        assert result == THEMES["Midnight"]

    def test_get_unknown_returns_default(self):
        result = get("NonExistent")
        assert result == THEMES[DEFAULT_THEME]

    def test_get_returns_dict(self):
        for name in THEMES:
            assert isinstance(get(name), dict)


class TestNames:
    def test_names_returns_list(self):
        result = names()
        assert isinstance(result, list)

    def test_names_contains_all_themes(self):
        result = names()
        assert set(result) == set(THEMES.keys())

    def test_names_count_matches_themes(self):
        assert len(names()) == len(THEMES)


class TestDisplayNames:
    def test_display_names_returns_list(self):
        result = display_names()
        assert isinstance(result, list)

    def test_display_names_count_matches_themes(self):
        assert len(display_names()) == len(THEMES)

    def test_display_names_match_theme_display_fields(self):
        expected = [THEMES[k]["display"] for k in THEMES]
        assert display_names() == expected


class TestNameFromDisplay:
    def test_returns_correct_name(self):
        for key, theme in THEMES.items():
            assert name_from_display(theme["display"]) == key

    def test_unknown_display_returns_default(self):
        assert name_from_display("No Such Theme") == DEFAULT_THEME

    def test_empty_string_returns_default(self):
        assert name_from_display("") == DEFAULT_THEME
