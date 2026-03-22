# Contributing to FreedomForge AI

First — thank you. This project exists to give everyone equal access to AI.
Every contribution, big or small, moves that mission forward.

---

## Who can contribute?

Everyone. You don't need to be a professional developer.

- Found a bug? Report it.
- Have an idea? Open a discussion.
- Know how to code? Pick an issue and go.
- Good at writing? Help improve the docs.
- Speak another language? Help with translations.

---

## Project structure

```
FreedomForgeAI/
├── main.py              Entry point — keep this minimal
├── core/                Engine room — AI, hardware, config, voice
├── ui/                  Everything the user sees and clicks
├── modules/             Feature add-ons (video, image, agent, etc.)
└── assets/              Icons and static files
```

The goal is that someone can add a new feature by adding ONE file
to `modules/` without touching anything else. Keep that clean.

---

## How to contribute

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test it works
5. Open a pull request with a clear description of what you changed and why

---

## Code style

- Clear is better than clever
- Comments should explain WHY, not what
- Every function should do one thing
- No hardcoded paths — use the config system
- Fail gracefully — never crash the whole app over one feature failing

---

## Adding a new module

1. Create `modules/yourmodule.py`
2. Implement a `handle(message, on_result, on_error)` function
3. Add trigger patterns to `modules/__init__.py`
4. Register in `ui/app.py`

That's it. The chat panel automatically gains the ability to use it.

---

## Reporting bugs

Open an issue with:
- What you were doing
- What you expected to happen
- What actually happened
- Your OS, RAM, and GPU (if any)

---

## A note from Ryan

> This is my first real project. I'm learning as I go.
> I built this because I believe everyone deserves access to AI —
> not just people who can afford subscriptions or understand terminals.
>
> If you're here, you believe that too.
> Welcome to the team.

---

*FreedomForge AI is dedicated to Miranda.*
*She will never be forgotten.*
