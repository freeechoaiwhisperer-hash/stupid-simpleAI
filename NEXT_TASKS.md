# FreedomForge AI — Next Tasks for DeepSeek / Claude Code

> This file is a brief for your next AI coding session.
> Each task is self-contained. Paste the task + relevant file(s) into DeepSeek or Claude Code.

---

## ✅ Already Done (this session)

- `multi_agent` module registered in `ui/app.py` → `/scout` and `/plan` now route to it live
- `IntegrityChecker` wired into `main.py` → builds SHA-256 manifest on first launch, warns on tampering
- `MemoryManager` wired into `ui/chat.py` → conversation persists across restarts under `~/.free_echo/memory/`
- `FreedomForgeAI_fixed.zip` removed from git tracking

---

## 🔲 Task 1 — File Sort Cleaner UI Panel (Priority: HIGH)

**What it is:** The backend (`plugins/echo_file_sort_cleaner.py`) is 100% complete.
It can scan a folder, hash every file, find duplicates, sort into typed sub-folders,
take a before-snapshot, and restore from it.

**What's missing:** A UI panel so users can actually use it.

**Spec:**
- New file: `ui/file_cleaner_tab.py`
- Same structure as existing panels (`PrivacyPanel`, `ModelsPanel`, etc.)
- Sections:
  1. **Folder picker** — `filedialog.askdirectory()` button + label showing chosen path
  2. **Scan** — button triggers `EchoFileSortCleaner(path).scan()`, shows count of
     files found, duplicates found, total size in a results card
  3. **Preview** — list of what would move where (read from scan result)
  4. **Organise** — button triggers `.make_snapshot()` then `.organise()`,
     shows progress, shows "Done — X files sorted, Y duplicates moved"
  5. **Restore** — button triggers `.restore_from_snapshot()`, confirms with a dialog first

- Register it in `ui/app.py` the same way other panels are registered:
  ```python
  from ui.file_cleaner_tab import FileCleanerPanel
  # in _build_ui():
  self.cleaner_panel = FileCleanerPanel(self.content_frame, self, T)
  self.panels["Files"] = self.cleaner_panel
  # add nav button: ("🗂️", "Files", "Files")
  ```

**Files to give Claude/DeepSeek:**
- `plugins/echo_file_sort_cleaner.py` (the backend)
- `ui/privacy_tab.py` (example of a similar panel with sections + cards)
- `ui/app.py` (so it knows how panels are registered)
- `assets/themes.py` (so it uses theme dict properly)

---

## 🔲 Task 2 — Windows Install Script (Priority: HIGH)

**What it is:** `setup.sh` works on Linux. Windows users have no equivalent.

**Spec:**
- New file: `install.bat`
- Should:
  1. Check `python --version` is 3.8+, error and link to python.org if not
  2. Run `pip install -r requirements.txt`
  3. Create `FreedomForgeAI.bat` in the same folder that runs `python main.py`
  4. Offer to create a desktop shortcut (copy the .bat to `%USERPROFILE%\Desktop`)
  5. Print colored success/error messages with `echo` + ANSI or plain text
  6. At the end, say "Run FreedomForgeAI.bat to start the app"

- Also create `install.command` (Mac equivalent — same steps with `python3`)

**Files to give Claude/DeepSeek:**
- `setup.sh` (Linux version to match the style)
- `requirements.txt`

---

## 🔲 Task 3 — Real ComfyUI Wan2.1 Workflow (Priority: MEDIUM)

**What it is:** `modules/video.py` correctly detects if ComfyUI is running,
but the `_build_workflow()` function is a placeholder stub that sends a
broken 1-node workflow. When ComfyUI IS running, video generation will fail.

**Spec:**
- Replace `_build_workflow()` in `modules/video.py` with a real Wan2.1 workflow
- The workflow JSON should:
  - Accept `prompt` (positive text) and `generator` (string key)
  - Include the standard Wan2.1 node graph (CLIPTextEncode × 2, KSampler,
    VAEDecode, SaveImage, etc.)
  - Support AnimateDiff as a second path if `generator == "animatediff"`
- Add a `negative_prompt` parameter with a sensible default
- After submitting, poll `GET /history/{prompt_id}` every 2 seconds and
  call `on_status` with progress updates until complete

**Files to give Claude/DeepSeek:**
- `modules/video.py` (current stub)
- Tell it: "Use the standard ComfyUI API. Wan2.1 text-to-video node graph."

---

## 🔲 Task 4 — Memory Stats in Privacy/Settings Panel (Priority: MEDIUM)

**What it is:** The `MemoryManager` has a `.stats()` method that returns
`{rolling_entries, summary_entries, memory_dir}`. This should be visible in the UI.

**Spec:**
- In `ui/privacy_tab.py`, add a new section "🧠  Chat Memory"
- Show: rolling entries count, summary entries count, memory directory path
- Add a "Clear Memory" button that calls `get_memory_manager().clear()`
  and refreshes the stats display
- Add a "Mark Important" text field — user types a phrase, clicks "Mark",
  calls `get_memory_manager().mark_important(phrase)`, shows count updated

**Files to give Claude/DeepSeek:**
- `ui/privacy_tab.py` (existing panel — add a section to it)
- `core/memory_manager.py` (the API)

---

## 🔲 Task 5 — Control Key UI in Settings (Priority: MEDIUM)

**What it is:** `modules/security_guard.ControlKey` exists but there is no
UI to set, verify, or clear it.

**Spec:**
- In `ui/settings.py`, add a "🔑  Control Key" section
- If no key is set: show "No control key set" + a text field + "Set Key" button
  that calls `get_control_key().set_key(text)`
- If key is set: show "Control key is active" + text field + "Verify" button
  + "Remove Key" button (remove requires entering current key first)
- The control key should gate agent mode — in `ui/app.py`'s `_toggle_agent()`,
  check `get_control_key().verify(prompt_for_key())` before enabling

**Files to give Claude/DeepSeek:**
- `ui/settings.py` (add a section)
- `modules/security_guard.py` (the ControlKey API)

---

## 🔲 Task 6 — Forge Tool Library Chat Commands (Priority: LOW)

**What it is:** `core/tool_repo.py` is built and tested but inaccessible to users.

**Spec:**
- Add trigger patterns to `modules/__init__.py`:
  ```python
  "forge": [
      r"^/forge\b",
      r"\bforge\s+(tool|library|list|run)\b",
  ]
  ```
- Create `modules/forge.py` with:
  - `/forge list` → calls `get_tool_repo().list_tools()`, formats as table
  - `/forge run <name>` → calls `get_tool_repo().run_tool(name)`, shows output
  - `/forge delete <name>` → calls `get_tool_repo().delete_tool(name)`
  - `/forge info <name>` → shows tool metadata from `list_tools()`
- Register `forge` module in `ui/app.py`

**Files to give Claude/DeepSeek:**
- `core/tool_repo.py` (the API)
- `modules/weather.py` (simplest module — use as template for forge.py)
- `modules/__init__.py` (add the triggers here)

---

## 📋 Summary Table

| Task | File(s) to Create/Edit | Effort | Impact |
|------|----------------------|--------|--------|
| File Cleaner UI | `ui/file_cleaner_tab.py` + `ui/app.py` | ~150 lines | High — makes Phase 4 live |
| Windows/Mac installer | `install.bat`, `install.command` | ~60 lines each | High — opens Windows users |
| ComfyUI real workflow | `modules/video.py` | ~80 lines | Medium — fixes video |
| Memory stats in Privacy | `ui/privacy_tab.py` | ~40 lines | Medium — shows memory is working |
| Control Key UI | `ui/settings.py` + `ui/app.py` | ~60 lines | Medium — security feature visible |
| Forge tool commands | `modules/forge.py` + `modules/__init__.py` + `ui/app.py` | ~80 lines | Low — power-user feature |

**Recommended order:** Task 1 → Task 2 → Task 3 → Task 4+5 → Task 6
