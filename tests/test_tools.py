"""Tests for modules/tools.py — ToolRepo"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tools import ToolRepo


class TestToolRepoInit:
    def test_initializes_with_empty_tools(self):
        repo = ToolRepo()
        assert repo.tools == {}


class TestAddTool:
    def test_add_single_tool(self):
        repo = ToolRepo()
        repo.add_tool("greet", lambda: "hello")
        assert "greet" in repo.tools

    def test_add_multiple_tools(self):
        repo = ToolRepo()
        repo.add_tool("a", 1)
        repo.add_tool("b", 2)
        assert "a" in repo.tools
        assert "b" in repo.tools

    def test_add_tool_overwrites_existing(self):
        repo = ToolRepo()
        repo.add_tool("calc", lambda: 1)
        repo.add_tool("calc", lambda: 2)
        assert repo.tools["calc"]() == 2

    def test_tool_value_is_preserved(self):
        repo = ToolRepo()
        tool = object()
        repo.add_tool("obj", tool)
        assert repo.tools["obj"] is tool


class TestGetTool:
    def test_get_existing_tool(self):
        repo = ToolRepo()
        repo.add_tool("ping", "pong")
        assert repo.get_tool("ping") == "pong"

    def test_get_missing_tool_returns_none(self):
        repo = ToolRepo()
        assert repo.get_tool("missing") is None

    def test_get_tool_returns_callable(self):
        repo = ToolRepo()
        fn = lambda x: x * 2
        repo.add_tool("double", fn)
        retrieved = repo.get_tool("double")
        assert retrieved(5) == 10

    def test_get_nonexistent_tool_returns_none(self):
        repo = ToolRepo()
        assert repo.get_tool("never_added") is None
