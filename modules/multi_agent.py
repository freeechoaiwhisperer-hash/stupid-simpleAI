# ============================================================
#  FreedomForge AI — modules/multi_agent.py
#  Smart Scout — multi-step task planner & executor
#
#  Vision:
#  When a user request is too complex for a single model call,
#  the Smart Scout breaks it into sub-tasks, routes each to
#  the appropriate specialist (coder, researcher, summarizer),
#  collects their outputs, and assembles a final answer.
#
#  This module sits *above* raw models and can:
#  - Split goals into ordered steps.
#  - Retry failed steps with a different approach.
#  - Log every sub-step so the user always knows what is running.
#  - Sandbox code execution via core.tool_repo.
# ============================================================

import threading
from typing import Callable, List

from core import logger, model_manager
from core.tool_repo import get_tool_repo

MODULE_NAME = "multi_agent"

# ── Sub-task types ───────────────────────────────────────────

_STEP_PROMPTS = {
    "plan": (
        "You are a task planner.  Break the following user request "
        "into a numbered list of clear sub-tasks.  Output ONLY the "
        "numbered list, one task per line.\n\nRequest: {goal}"
    ),
    "code": (
        "You are an expert programmer.  Write Python code to complete "
        "the following task.  Output ONLY the code, no explanation.\n\n"
        "Task: {goal}"
    ),
    "research": (
        "You are a research assistant.  Answer the following question "
        "concisely and accurately, using your training knowledge.\n\n"
        "Question: {goal}"
    ),
    "summarize": (
        "You are a summarizer.  Condense the following text into a "
        "clear, brief summary that preserves all key information.\n\n"
        "Text:\n{goal}"
    ),
}


def _classify_step(step_text: str) -> str:
    """Heuristic: decide which specialist handles a step."""
    lower = step_text.lower()
    if any(w in lower for w in ("write code", "create script",
                                 "implement", "program", "python",
                                 "bash", "shell")):
        return "code"
    if any(w in lower for w in ("summarize", "condense", "brief",
                                 "overview")):
        return "summarize"
    return "research"


def _call_model(prompt: str) -> str:
    """
    Run a single synchronous model inference.
    Returns the full reply text, or an error string.
    """
    result_holder: List[str] = []
    done_event = threading.Event()

    def on_token(token: str) -> None:
        result_holder.append(token)

    def on_complete() -> None:
        done_event.set()

    def on_error(err: str) -> None:
        result_holder.append(f"[ERROR: {err}]")
        done_event.set()

    if not model_manager.is_model_loaded():
        return "[No model loaded — cannot run sub-task]"

    model_manager.generate_stream(
        messages   = [{"role": "user", "content": prompt}],
        on_token   = on_token,
        on_complete = on_complete,
        on_error   = on_error,
    )
    done_event.wait(timeout=120)
    return "".join(result_holder)


def run_smart_scout(
    goal:       str,
    on_status:  Callable[[str], None],
    on_result:  Callable[[str], None],
    on_error:   Callable[[str], None],
    max_steps:  int = 6,
) -> None:
    """
    Main entry point.  Runs entirely in a background thread so the
    UI stays responsive.

    Flow:
    1. Ask the planner model to split *goal* into sub-tasks.
    2. Execute each sub-task with the appropriate specialist.
    3. Collect outputs and assemble a final answer.
    4. If a step produces code, register it with ToolRepo.
    """

    def _run() -> None:
        try:
            # ── Step 1: Plan ─────────────────────────────────
            on_status("🧭  Planning sub-tasks…")
            plan_prompt = _STEP_PROMPTS["plan"].format(goal=goal)
            plan_text   = _call_model(plan_prompt)

            if "[ERROR" in plan_text:
                on_error(f"Planner failed: {plan_text}")
                return

            steps = _parse_steps(plan_text, max_steps)
            logger.info(
                f"MultiAgent: planned {len(steps)} step(s) for: {goal[:60]}"
            )

            if not steps:
                # Fall back to a single research step
                steps = [goal]

            # ── Step 2: Execute each step ─────────────────────
            step_outputs: List[str] = []
            repo = get_tool_repo()

            for idx, step in enumerate(steps, 1):
                on_status(
                    f"🔧  Step {idx}/{len(steps)}: {step[:60]}…"
                )
                step_type = _classify_step(step)
                prompt    = _STEP_PROMPTS[step_type].format(goal=step)
                output    = _call_model(prompt)

                if "[ERROR" in output:
                    logger.warning(
                        f"MultiAgent: step {idx} errored: {output[:80]}"
                    )
                    step_outputs.append(
                        f"Step {idx} ({step_type}): [failed — {output[:120]}]"
                    )
                    continue

                step_outputs.append(f"Step {idx} ({step_type}):\n{output}")

                # Auto-register generated code with ToolRepo
                if step_type == "code" and len(output.strip()) > 20:
                    tool_name = _slug(step)[:40] or f"step_{idx}_tool"
                    _register_code(repo, tool_name, step, output)

            # ── Step 3: Assemble final answer ─────────────────
            on_status("📝  Assembling final answer…")
            combined = "\n\n---\n\n".join(step_outputs)

            if len(steps) > 1:
                summary_prompt = _STEP_PROMPTS["summarize"].format(
                    goal=combined
                )
                final = _call_model(summary_prompt)
                if "[ERROR" in final:
                    final = combined        # fallback: return raw outputs
            else:
                final = step_outputs[0] if step_outputs else "(no output)"

            on_result(final)

        except Exception as exc:
            logger.exception(f"MultiAgent: unexpected error: {exc}")
            on_error(f"Smart Scout error: {exc}")

    threading.Thread(target=_run, daemon=True).start()


# ── Module router entry point ─────────────────────────────────

def handle(
    message:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Called by modules/__init__.py router."""

    def on_status(text: str) -> None:
        on_result(text)          # stream status updates as incremental results

    # Strip command prefix if present
    goal = message
    for prefix in ["/agent ", "/scout ", "/plan "]:
        if message.lower().startswith(prefix):
            goal = message[len(prefix):].strip()
            break

    if not goal:
        on_error("Please describe what you want the Smart Scout to do.")
        return

    run_smart_scout(
        goal      = goal,
        on_status = on_status,
        on_result = on_result,
        on_error  = on_error,
    )


# ── Helpers ──────────────────────────────────────────────────

def _parse_steps(plan_text: str, max_steps: int) -> List[str]:
    """Extract numbered list items from planner output."""
    steps = []
    for line in plan_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Accept  "1. Do X"  or  "1) Do X"  or  "- Do X"
        if line and (line[0].isdigit() or line[0] == "-"):
            # Strip leading number/bullet
            text = line.lstrip("0123456789.-) ").strip()
            if text:
                steps.append(text)
        if len(steps) >= max_steps:
            break
    return steps


def _slug(text: str) -> str:
    """Convert text to a safe identifier string."""
    import re
    return re.sub(r"[^a-z0-9_]", "_", text.lower())[:48]


def _register_code(repo, tool_name: str, description: str, code: str) -> None:
    """Register generated code with ToolRepo; silently ignore errors."""
    try:
        # Strip markdown fences if the model wrapped the code
        import re
        match = re.search(r"```(?:python)?\n?(.*?)```", code, re.DOTALL)
        clean = match.group(1).strip() if match else code.strip()
        if clean:
            repo.register_tool(
                name        = tool_name,
                description = description,
                language    = "python",
                code        = clean,
                created_by  = "MultiAgent",
            )
    except Exception as exc:
        logger.warning(f"MultiAgent: could not register tool: {exc}")
