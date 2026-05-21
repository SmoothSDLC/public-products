---
name: install-claw-compactor
description: >
  Use this skill when setting up claw-compactor context-compaction hooks for Claude Code,
  Codex, GitHub Copilot, or VSCode. Triggers on: "install claw-compactor",
  "set up context compaction hooks", "configure agent hooks for Reservoir context",
  "agents aren't getting compacted context", "hook up claw-compactor for cloud agents",
  "bootstrap agent context hooks", "set up hooks for a new agent environment", even if
  the user does not mention claw-compactor by name. Installs hook scripts into
  `.agent/hooks/`, merges provider hook configs in `.claude/settings.json`,
  `.codex/hooks.json`, `.github/hooks/hooks.json`, and `.vscode/agents/hooks.json`, and
  updates `.gitignore` and `.github/copilot-instructions.md`. Supports selective
  per-provider installation via optional argument. The installer is idempotent — safe
  to re-run.
license: Proprietary
compatibility: >
  Requires Python 3.8+ (python, python3, or py in PATH) and Node.js (node in PATH).
  Runs on Windows, macOS, and Linux. Works in local dev and cloud CI agents.
metadata:
  team: platform-delivery
  version: "2.0"
---

# install-claw-compactor

Sets up claw-compactor context-compaction hooks for Claude Code, Codex, GitHub Copilot, and VSCode.

---

## Purpose

Context grows large during long agent sessions. claw-compactor hooks fire on
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and `PostToolBatch`
to write a compacted context snapshot to `.reservoir/compacted-context.md`. Agents
use that file instead of re-reading the full context bundle, keeping responses fast
and within token limits.

This skill installs:
- `.agent/hooks/compact-context.py` — hook body (provider-aware, fail-open)
- `.agent/hooks/compact-context.js` — cross-platform launcher (finds python3/python/py)
- Provider configs: `.claude/settings.json`, `.codex/hooks.json`, `.github/hooks/hooks.json`, `.vscode/agents/hooks.json`
- Provider-specific skills: `.claude/skills/token-savings/`, `.codex/skills/token-savings/`, `.github/skills/token-savings/`, `.vscode/agents/skills/token-savings/`
- `.gitignore` additions (hook output, virtualenv, npm cache)
- `.github/copilot-instructions.md` pointer to the compacted-context file

---

## Prerequisites

- Python 3.8+ available as `python`, `python3`, or `py` in PATH
- Node.js (`node`) in PATH — required by the hook launcher at runtime
- Run from the target repository root (directory with `.git/`)
- `pip` available — the hook auto-installs `claw-compactor` on first use if missing

---

## Workflow

Progress:
- [ ] Step 1: Run the installer from the repo root
- [ ] Step 2: Verify hook files installed in `.agent/hooks/`
- [ ] Step 3: Verify provider configs updated
- [ ] Step 4: Validate skill integrity

**Step 1 — Run installer:**

Auto-detect providers in the repo (installs for all detected):
```bash
python .agent/skills/install-claw-compactor/scripts/run.py
```

Or install for a specific provider:
```bash
# Install for Claude Code only
python .agent/skills/install-claw-compactor/scripts/run.py claude

# Install for Codex only
python .agent/skills/install-claw-compactor/scripts/run.py codex

# Install for GitHub Copilot only
python .agent/skills/install-claw-compactor/scripts/run.py copilot

# Install for VSCode agent only
python .agent/skills/install-claw-compactor/scripts/run.py vscode
```

If only `python3` is available, use `python3` instead of `python`.

**Step 2 — Verify hooks:**
```bash
ls .agent/hooks/
# Expected: compact-context.js  compact-context.py
```

**Step 3 — Verify provider configs:**
```bash
# Claude: .claude/settings.json should have hooks for SessionStart, UserPromptSubmit,
#          PreToolUse, PostToolUse, PostToolBatch
# Codex:  .codex/hooks.json should have hooks for SessionStart, PreToolUse, PostToolUse
# Copilot: .github/hooks/hooks.json should have hooks for sessionStart, preToolUse, postToolUse
# VSCode:  .vscode/agents/hooks.json should have hooks for sessionStart, preToolUse, postToolUse

# Verify skills installed to provider-specific locations:
ls .claude/skills/token-savings/    # Claude Code skill
ls .codex/skills/token-savings/     # Codex skill
ls .github/skills/token-savings/    # Copilot skill
ls .vscode/agents/skills/token-savings/  # VSCode skill
```

**Step 4 — Validate:**
```bash
python .agent/skills/install-claw-compactor/scripts/validate-skill.py
```

---

## Gotchas

- **Provider auto-detection**: If no provider argument is specified, the script detects providers by checking for config directories (`.claude/`, `.codex/`, `.github/`, `.vscode/`). If none are found, the script errors and requires an explicit provider.
- **Invalid provider argument**: Specifying an invalid provider (e.g., `python run.py invalid`) exits with error code 1 and shows the help text.
- **`.claude/settings.local.json` is user-specific**: Do not commit it. Add it to `.gitignore`. Project-level hook config lives in `.claude/settings.json`.
- **JS launcher uses `__dirname`**: `compact-context.js` must be in the same directory as `compact-context.py` at runtime (`.agent/hooks/`). The skill's `assets/` copies are templates only.
- **Hook fail-open is intentional**: If claw-compactor is not installed or Reservoir is unavailable, the hook exits 0 silently. This prevents hooks from blocking agent startup.
- **Cloud agents — first-run latency**: On cold start the hook attempts `pip install claw-compactor` inline (timeout 120s). Pre-install in the CI environment image to avoid this.
- **Idempotent merge**: Re-running the installer after a manual config edit restores the hook entry without duplicating it.
