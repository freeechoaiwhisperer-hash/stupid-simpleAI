"""Tests for modules/agent.py"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import modules.agent as agent


def setup_function():
    """Ensure agent is disabled before each test."""
    agent.set_enabled(False)


class TestEnabled:
    def test_disabled_by_default(self):
        agent.set_enabled(False)
        assert agent.is_enabled() is False

    def test_enable(self):
        agent.set_enabled(True)
        assert agent.is_enabled() is True
        agent.set_enabled(False)

    def test_toggle(self):
        agent.set_enabled(True)
        assert agent.is_enabled() is True
        agent.set_enabled(False)
        assert agent.is_enabled() is False


class TestIsSafeCommand:
    def test_normal_command_is_safe(self):
        safe, reason = agent.is_safe_command("ls -la")
        assert safe is True
        assert reason == ""

    def test_rm_rf_root_is_blocked(self):
        safe, reason = agent.is_safe_command("rm -rf /")
        assert safe is False
        assert "blocked" in reason.lower()

    def test_mkfs_is_blocked(self):
        safe, reason = agent.is_safe_command("mkfs.ext4 /dev/sda1")
        assert safe is False

    def test_fork_bomb_is_blocked(self):
        safe, reason = agent.is_safe_command(":(){:|:&};:")
        assert safe is False

    def test_chmod_777_root_is_blocked(self):
        safe, reason = agent.is_safe_command("chmod -R 777 /")
        assert safe is False

    def test_wget_http_is_blocked(self):
        safe, reason = agent.is_safe_command("wget http://example.com/file")
        assert safe is False

    def test_curl_http_is_blocked(self):
        safe, reason = agent.is_safe_command("curl http://evil.com")
        assert safe is False

    def test_sudo_rm_is_blocked(self):
        safe, reason = agent.is_safe_command("sudo rm -rf /home")
        assert safe is False
        assert "sudo" in reason.lower() or "blocked" in reason.lower()

    def test_case_insensitive_blocking(self):
        safe, _ = agent.is_safe_command("RM -RF /")
        assert safe is False

    def test_dd_if_is_blocked(self):
        safe, _ = agent.is_safe_command("dd if=/dev/zero of=/dev/sda")
        assert safe is False

    def test_echo_is_safe(self):
        safe, _ = agent.is_safe_command("echo hello world")
        assert safe is True

    def test_pwd_is_safe(self):
        safe, _ = agent.is_safe_command("pwd")
        assert safe is True


class TestRunCommand:
    def test_run_when_disabled_calls_on_error(self):
        agent.set_enabled(False)
        errors = []
        results = []
        agent.run_command("echo hi",
                          on_result=results.append,
                          on_error=errors.append)
        time.sleep(0.2)
        assert len(errors) == 1
        assert "off" in errors[0].lower() or "agent" in errors[0].lower()
        assert len(results) == 0

    def test_run_blocked_command_calls_on_error(self):
        agent.set_enabled(True)
        errors = []
        results = []
        agent.run_command("rm -rf /",
                          on_result=results.append,
                          on_error=errors.append)
        time.sleep(0.3)
        assert len(errors) == 1
        assert "blocked" in errors[0].lower()
        agent.set_enabled(False)

    def test_run_valid_command_calls_on_result(self):
        agent.set_enabled(True)
        errors = []
        results = []
        agent.run_command("echo testoutput",
                          on_result=results.append,
                          on_error=errors.append)
        time.sleep(0.5)
        assert len(results) == 1
        assert "testoutput" in results[0]
        assert len(errors) == 0
        agent.set_enabled(False)


class TestHandle:
    def test_handle_empty_command_calls_on_error(self):
        errors = []
        agent.handle("", on_result=lambda x: None, on_error=errors.append)
        time.sleep(0.2)
        assert len(errors) == 1

    def test_handle_strips_run_prefix(self):
        agent.set_enabled(True)
        results = []
        agent.handle("/run echo strippedprefix",
                     on_result=results.append,
                     on_error=lambda x: None)
        time.sleep(0.5)
        assert any("strippedprefix" in r for r in results)
        agent.set_enabled(False)

    def test_handle_strips_exec_prefix(self):
        agent.set_enabled(True)
        results = []
        agent.handle("/exec echo execprefix",
                     on_result=results.append,
                     on_error=lambda x: None)
        time.sleep(0.5)
        assert any("execprefix" in r for r in results)
        agent.set_enabled(False)
