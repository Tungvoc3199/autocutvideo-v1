# AGENTS.md — Codex Operating Instructions

## Working mode
- Treat this repository as a Windows 11, Python-first, CLI-first automation workspace.
- Work in an isolated Git branch or Codex Worktree. Do not implement directly on `main`.
- Before coding, read the relevant task file under `.codex/tasks/`, inspect the current repository, and write a concise implementation checklist.
- Prefer a minimal safe change that produces a runnable baseline. Do not refactor unrelated legacy code.

## Engineering baseline
- Target Python 3.11+ on Windows 11.
- Use FFmpeg and FFprobe as external command-line dependencies. Detect missing binaries and show actionable Vietnamese error messages.
- Keep secrets out of Git. Use `.env.example` for environment variable names only. Never commit API keys, tokens, cookies, or credentials.
- Use `pathlib` and subprocess argument lists so Windows paths with spaces work correctly.
- Preserve resumability: state files, deterministic output folders, and skip completed steps unless `--force` is supplied.
- Add logs, checkpoints, test cases, and rollback notes.

## Documentation baseline
For each new tool or module, include:
- `README.md`: installation, Windows setup, commands, outputs, troubleshooting.
- `PROJECT.md`: objective, scope, constraints, success criteria.
- `STATE.md`: current status, completed items, pending items, known limitations.
- `CHANGELOG.md`: dated changes and rollback instructions.
- `.env.example`: environment variable names without secrets.

## Verification baseline
- Add unit tests for pure logic and mocked subprocess calls.
- Run `python -m pytest -q`.
- Run `python -m compileall` on the new package.
- If FFmpeg or model dependencies are unavailable in the sandbox, document the limitation honestly and still test the code paths that can be verified locally.

## Product constraints
- Prioritize a tool that increases content output and saves manual editing time.
- The user must only process videos they own, license, or have permission to adapt.
- Do not add platform scraping, CAPTCHA bypass, account automation, or credential storage.
