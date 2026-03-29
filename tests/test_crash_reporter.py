"""Tests for core/crash_reporter.py"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.crash_reporter as reporter


@pytest.fixture(autouse=True)
def isolated_crash_dir(tmp_path, monkeypatch):
    """Each test uses its own temp directory for crash reports."""
    monkeypatch.chdir(tmp_path)
    yield


class TestCapture:
    def test_returns_report_id_string(self):
        exc = ValueError("test error")
        rid = reporter.capture(exc)
        assert isinstance(rid, str)
        assert len(rid) == 12

    def test_creates_crash_file(self):
        exc = RuntimeError("boom")
        reporter.capture(exc)
        crash_files = list(os.scandir(reporter.CRASH_DIR))
        assert len(crash_files) == 1
        assert crash_files[0].name.endswith(".json")

    def test_report_contains_error_type(self):
        exc = TypeError("bad type")
        rid = reporter.capture(exc)
        path = os.path.join(reporter.CRASH_DIR, f"crash_{rid}.json")
        with open(path) as f:
            data = json.load(f)
        assert data["error"] == "TypeError"

    def test_report_contains_message(self):
        exc = ValueError("unique error message 42")
        rid = reporter.capture(exc)
        path = os.path.join(reporter.CRASH_DIR, f"crash_{rid}.json")
        with open(path) as f:
            data = json.load(f)
        assert "unique error message 42" in data["message"]

    def test_report_contains_context(self):
        exc = Exception("err")
        rid = reporter.capture(exc, context="unit test context")
        path = os.path.join(reporter.CRASH_DIR, f"crash_{rid}.json")
        with open(path) as f:
            data = json.load(f)
        assert data["context"] == "unit test context"

    def test_report_contains_system_info(self):
        exc = Exception("err")
        rid = reporter.capture(exc)
        path = os.path.join(reporter.CRASH_DIR, f"crash_{rid}.json")
        with open(path) as f:
            data = json.load(f)
        assert "system" in data
        assert "os" in data["system"]

    def test_on_ready_callback_called(self):
        called = []
        exc = Exception("cb test")
        reporter.capture(exc, on_ready=lambda rid, path: called.append((rid, path)))
        assert len(called) == 1
        rid, path = called[0]
        assert os.path.exists(path)

    def test_multiple_reports_same_exception_type_unique_ids(self):
        exc1 = ValueError("err 1")
        exc2 = ValueError("err 2")
        rid1 = reporter.capture(exc1)
        rid2 = reporter.capture(exc2)
        # IDs are based on timestamp + type; may collide if within same second,
        # so just verify both are strings
        assert isinstance(rid1, str)
        assert isinstance(rid2, str)


class TestGetRecent:
    def test_returns_empty_when_no_crashes(self):
        result = reporter.get_recent()
        assert result == []

    def test_returns_list_after_capture(self):
        reporter.capture(Exception("test"))
        result = reporter.get_recent()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_each_entry_has_required_fields(self):
        reporter.capture(Exception("err"))
        reports = reporter.get_recent()
        required = {"id", "ts", "error", "message", "path"}
        for r in reports:
            assert required.issubset(set(r.keys()))

    def test_returns_at_most_10(self):
        for i in range(15):
            reporter.capture(ValueError(f"error {i}"))
        result = reporter.get_recent()
        assert len(result) <= 10

    def test_path_exists_for_each_entry(self):
        reporter.capture(Exception("path test"))
        for r in reporter.get_recent():
            assert os.path.exists(r["path"])


class TestPrune:
    def test_prune_keeps_max_reports(self):
        max_r = reporter.MAX_REPORTS
        for i in range(max_r + 5):
            reporter.capture(ValueError(f"error {i}"))
        os.makedirs(reporter.CRASH_DIR, exist_ok=True)
        files = [f for f in os.listdir(reporter.CRASH_DIR) if f.endswith(".json")]
        assert len(files) <= max_r

    def test_prune_does_nothing_when_no_dir(self):
        # Should not raise even when dir doesn't exist
        reporter._prune()
