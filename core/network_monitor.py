# ============================================================
#  FreedomForge AI — core/network_monitor.py
#  Network monitoring and kill switch
#  Shows what's talking in/out. One button cuts everything.
# ============================================================

import subprocess
import threading
import platform
from typing import Callable, Optional
from core import logger

_kill_active  = False
_monitor_cb: Optional[Callable] = None


# ── Connection info ──────────────────────────────────────────

def get_connections() -> list:
    """
    Returns list of active network connections.
    Each item: {pid, name, local, remote, status}
    """
    try:
        import psutil
        conns = []
        for conn in psutil.net_connections(kind="inet"):
            try:
                proc_name = ""
                if conn.pid:
                    try:
                        proc_name = psutil.Process(conn.pid).name()
                    except Exception:
                        proc_name = f"PID {conn.pid}"

                local  = f"{conn.laddr.ip}:{conn.laddr.port}" \
                         if conn.laddr else "—"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" \
                         if conn.raddr else "—"

                conns.append({
                    "pid":    conn.pid,
                    "name":   proc_name,
                    "local":  local,
                    "remote": remote,
                    "status": conn.status,
                })
            except Exception:
                continue
        return sorted(conns, key=lambda x: x["name"])
    except Exception as e:
        logger.error(f"get_connections error: {e}")
        return []


def get_bandwidth() -> dict:
    """Returns current network bytes sent/recv."""
    try:
        import psutil
        stats = psutil.net_io_counters()
        return {
            "bytes_sent": stats.bytes_sent,
            "bytes_recv": stats.bytes_recv,
            "mb_sent":    round(stats.bytes_sent / (1024**2), 1),
            "mb_recv":    round(stats.bytes_recv / (1024**2), 1),
        }
    except Exception:
        return {"bytes_sent": 0, "bytes_recv": 0,
                "mb_sent": 0, "mb_recv": 0}


# ── Network kill switch ──────────────────────────────────────

def is_kill_active() -> bool:
    return _kill_active


def kill_network(
    on_done:  Callable[[bool, str], None] = None,
) -> None:
    """
    Cut ALL internet traffic immediately.
    Uses OS firewall rules — works on Linux, Mac, Windows.
    """
    global _kill_active

    def _kill():
        global _kill_active
        system = platform.system()
        try:
            if system == "Linux":
                # Block all outbound and inbound with iptables
                cmds = [
                    ["sudo", "iptables", "-I", "OUTPUT", "1",
                     "-j", "DROP"],
                    ["sudo", "iptables", "-I", "INPUT", "1",
                     "-j", "DROP"],
                ]
            elif system == "Darwin":  # Mac
                cmds = [
                    ["sudo", "pfctl", "-e"],
                    ["sudo", "sh", "-c",
                     'echo "block all" | pfctl -f -'],
                ]
            elif system == "Windows":
                cmds = [
                    ["netsh", "advfirewall", "set",
                     "allprofiles", "firewallpolicy",
                     "blockinbound,blockoutbound"],
                ]
            else:
                if on_done:
                    on_done(False, f"Unsupported OS: {system}")
                return

            for cmd in cmds:
                subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10,
                )

            _kill_active = True
            logger.warning("NETWORK KILL SWITCH ACTIVATED")
            if on_done:
                on_done(True, "All network traffic blocked.")

        except Exception as e:
            logger.error(f"Kill switch error: {e}")
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_kill, daemon=True).start()


def restore_network(
    on_done: Callable[[bool, str], None] = None,
) -> None:
    """Restore normal network access."""
    global _kill_active

    def _restore():
        global _kill_active
        system = platform.system()
        try:
            if system == "Linux":
                cmds = [
                    ["sudo", "iptables", "-D", "OUTPUT",
                     "-j", "DROP"],
                    ["sudo", "iptables", "-D", "INPUT",
                     "-j", "DROP"],
                ]
            elif system == "Darwin":
                cmds = [["sudo", "pfctl", "-d"]]
            elif system == "Windows":
                cmds = [
                    ["netsh", "advfirewall", "set",
                     "allprofiles", "firewallpolicy",
                     "blockinbound,allowoutbound"],
                ]
            else:
                if on_done:
                    on_done(False, f"Unsupported OS: {system}")
                return

            for cmd in cmds:
                subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10,
                )

            _kill_active = False
            logger.info("Network restored")
            if on_done:
                on_done(True, "Network access restored.")

        except Exception as e:
            logger.error(f"Restore network error: {e}")
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_restore, daemon=True).start()


# ── VPN helpers ──────────────────────────────────────────────

def check_vpn_installed() -> dict:
    """Check which VPN clients are installed."""
    result = {
        "mullvad":   False,
        "protonvpn": False,
        "wireguard": False,
        "openvpn":   False,
    }
    checks = {
        "mullvad":   ["mullvad", "version"],
        "protonvpn": ["protonvpn-cli", "--version"],
        "wireguard": ["wg", "--version"],
        "openvpn":   ["openvpn", "--version"],
    }
    for name, cmd in checks.items():
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                timeout=3,
            )
            result[name] = r.returncode == 0
        except Exception:
            pass
    return result


def get_vpn_status() -> dict:
    """Returns current VPN connection status."""
    result = {"connected": False, "provider": None, "ip": None}
    try:
        # Try mullvad
        r = subprocess.run(
            ["mullvad", "status"],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and "Connected" in r.stdout:
            result["connected"] = True
            result["provider"]  = "Mullvad"
            return result
    except Exception:
        pass
    try:
        # Try protonvpn
        r = subprocess.run(
            ["protonvpn-cli", "s"],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and "Connected" in r.stdout:
            result["connected"] = True
            result["provider"]  = "ProtonVPN"
            return result
    except Exception:
        pass
    return result
