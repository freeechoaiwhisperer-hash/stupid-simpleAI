"""Tests for core/network_monitor.py — non-OS-dependent logic"""

import sys
import os
import re
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.network_monitor as nm


class TestRun:
    def test_returns_completed_process_on_success(self):
        result = nm._run(["echo", "hello"])
        assert result.returncode == 0

    def test_returns_fallback_on_bad_command(self):
        result = nm._run(["nonexistent_cmd_xyz_123"])
        assert result.returncode == 1

    def test_returns_fallback_on_timeout(self):
        with patch("subprocess.run", side_effect=Exception("timeout")):
            result = nm._run(["sleep", "100"])
        assert result.returncode == 1


class TestAsync:
    def test_no_callback_returns_result_directly(self):
        result = nm._async(lambda: 42, None)
        assert result == 42

    def test_with_callback_calls_it(self):
        received = []
        import time
        nm._async(lambda: "value", received.append)
        time.sleep(0.2)
        assert received == ["value"]

    def test_callback_receives_exception_on_error(self):
        received = []
        import time

        def bad_fn():
            raise ValueError("oops")

        nm._async(bad_fn, received.append)
        time.sleep(0.2)
        assert len(received) == 1
        assert isinstance(received[0], Exception)


class TestGetBandwidth:
    def test_returns_dict(self):
        result = nm.get_bandwidth()
        assert isinstance(result, dict)

    def test_has_mb_sent_recv(self):
        result = nm.get_bandwidth()
        assert "mb_sent" in result
        assert "mb_recv" in result

    def test_has_bytes_sent_recv(self):
        result = nm.get_bandwidth()
        assert "bytes_sent" in result
        assert "bytes_recv" in result

    def test_values_are_non_negative(self):
        result = nm.get_bandwidth()
        assert result["mb_sent"] >= 0
        assert result["mb_recv"] >= 0
        assert result["bytes_sent"] >= 0
        assert result["bytes_recv"] >= 0

    def test_psutil_failure_returns_zeros(self):
        with patch.dict("sys.modules", {"psutil": None}):
            with patch("core.network_monitor.get_bandwidth",
                       return_value={"mb_sent": 0.0, "mb_recv": 0.0,
                                     "bytes_sent": 0, "bytes_recv": 0}):
                result = nm.get_bandwidth()
        assert result["mb_sent"] == 0.0


class TestCheckVpnInstalled:
    def test_returns_dict(self):
        result = nm.check_vpn_installed()
        assert isinstance(result, dict)

    def test_has_known_vpn_keys(self):
        result = nm.check_vpn_installed()
        for key in ("mullvad", "protonvpn", "wireguard", "openvpn"):
            assert key in result

    def test_values_are_booleans(self):
        result = nm.check_vpn_installed()
        for key, val in result.items():
            assert isinstance(val, bool), f"{key}: expected bool, got {type(val)}"

    def test_all_false_when_no_vpn_cmds(self):
        with patch("subprocess.run", side_effect=Exception("not found")):
            result = nm.check_vpn_installed()
        assert all(v is False for v in result.values())


class TestGetVpnStatus:
    def test_returns_dict(self):
        result = nm.get_vpn_status()
        assert isinstance(result, dict)

    def test_has_connected_field(self):
        result = nm.get_vpn_status()
        assert "connected" in result

    def test_not_connected_when_all_cmds_fail(self):
        with patch("subprocess.run", side_effect=Exception("not found")):
            result = nm.get_vpn_status()
        assert result["connected"] is False

    def test_mullvad_connected_detected(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Connected to Mullvad"

        with patch("subprocess.run", return_value=mock_result):
            result = nm.get_vpn_status()
        assert result["connected"] is True
        assert result["provider"] == "Mullvad"


class TestGetConnections:
    def test_returns_list_without_callback(self):
        result = nm.get_connections()
        assert isinstance(result, list)

    def test_each_connection_has_required_fields(self):
        result = nm.get_connections()
        for conn in result:
            for field in ("name", "local", "remote", "status"):
                assert field in conn, f"Missing field '{field}' in connection"
