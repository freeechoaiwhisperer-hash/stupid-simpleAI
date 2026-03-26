# ============================================================
#  FreedomForge AI — modules/agent.py
#  Computer control / agent module
# ============================================================

import subprocess
import threading
import shlex
from typing import Callable

MODULE_NAME = "agent"

# Patterns that are always blocked, regardless of agent mode.
# Checked against the lower-cased, stripped command string.
BLOCKED_PATTERNS = [
    # Destructive deletions
    "rm -rf /",
    "rm -rf ~",
    "rm -rf $home",
    "rm -fr /",
    "rm -fr ~",
    # Disk formatting / wiping
    "mkfs",
    "dd if=",
    "shred",
    "wipefs",
    # Fork bomb
    ":(){:|:&};:",
    # Dangerous chmod/chown on root
    "chmod -r 777 /",
    "chown -r root /",
    # Network download execution  — block both http and https
    "wget http",
    "curl http",
    "wget ftp",
    "curl ftp",
    # Process killers
    "pkill -9",
    "kill -9 1",
    "killall",
    # Privilege escalation helpers
    "sudo su",
    "sudo -i",
    "sudo bash",
    "sudo sh",
    # Python/shell self-modifying tricks
    "os.system",
    "subprocess.call",
    "eval(",
    "exec(",
]

_agent_enabled = False


def set_enabled(enabled: bool) -> None:
    global _agent_enabled
    _agent_enabled = enabled


def is_enabled() -> bool:
    return _agent_enabled


def is_safe_command(command: str) -> tuple[bool, str]:
    """Check if a command is safe to run. Returns (safe, reason)."""
    cmd_lower = command.lower().strip()

    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd_lower:
            return False, f"Blocked pattern: '{pattern}'"

    # Block any use of sudo rm (regardless of flags)
    if "sudo rm" in cmd_lower:
        return False, "sudo rm is blocked"

    return True, ""


def run_command(
    command:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Execute a shell command safely in a background thread."""

    def _run():
        if not _agent_enabled:
            on_error(
                "Agent Mode is OFF. Toggle it on in the top bar "
                "to allow command execution."
            )
            return

        safe, reason = is_safe_command(command)
        if not safe:
            on_error(f"Command blocked for safety: {reason}")
            return

        try:
            # Use shell=False with shlex.split() to prevent shell injection.
            # Fall back to a single-item list if splitting fails (e.g. empty).
            try:
                args = shlex.split(command)
            except ValueError:
                on_error(f"Could not parse command: {command}")
                return

            if not args:
                on_error("Empty command.")
                return

            result = subprocess.run(
                args,
                shell=False,          # No shell — prevents injection
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            on_result(
                f"```\n$ {command}\n{output}\n```\n"
                f"Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            on_error("Command timed out after 30 seconds")
        except FileNotFoundError:
            on_error(f"Command not found: {shlex.split(command)[0]}")
        except Exception as e:
            on_error(f"Command failed: {e}")

    threading.Thread(target=_run, daemon=True).start()


def handle(
    message:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Entry point called by module router."""
    command = message
    for prefix in ["/run ", "/exec "]:
        if message.lower().startswith(prefix):
            command = message[len(prefix):].strip()
            break

    if not command:
        on_error("Please provide a command to run.")
        return

    run_command(command, on_result, on_error)
