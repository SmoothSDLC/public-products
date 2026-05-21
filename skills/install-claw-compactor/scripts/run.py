#!/usr/bin/env python3
"""Install claw-compactor hooks for Claude, Codex, GitHub Copilot, and VSCode."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOK_PY_NAME = "compact-context.py"
HOOK_JS_NAME = "compact-context.js"

CLAUDE_EVENTS = {
    "SessionStart": {"matcher": "startup|resume|clear|compact", "timeout": 30},
    "UserPromptSubmit": {"timeout": 30},
    "PreToolUse": {"matcher": ".*", "timeout": 15},
    "PostToolUse": {"matcher": ".*", "timeout": 15},
    "PostToolBatch": {"timeout": 15},
}


def repo_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(read_text(path))


def write_json(path: Path, value: dict[str, Any]) -> None:
    write_text(path, json.dumps(value, indent=2) + "\n")


def ensure_claw_compactor() -> None:
    try:
        import claw_compactor  # noqa: F401
        return
    except Exception:
        pass

    base = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
    ]
    commands = [[*base, "claw-compactor"]]
    if sys.prefix == sys.base_prefix:
        commands.append([*base, "--user", "claw-compactor"])

    for command in commands:
        subprocess.run(command, check=False)
        try:
            import claw_compactor  # noqa: F401
            return
        except Exception:
            continue


def copy_hook_scripts(root: Path) -> None:
    source_hooks = Path(__file__).resolve().parent.parent / "assets"
    target_hooks = root / ".agent" / "hooks"
    target_hooks.mkdir(parents=True, exist_ok=True)
    for file_name in (HOOK_PY_NAME, HOOK_JS_NAME):
        source = (source_hooks / file_name).resolve()
        target = (target_hooks / file_name).resolve()
        if source == target:
            continue
        shutil.copy2(source, target)


def hook_command(provider: str, event: str) -> str:
    return f"node .agent/hooks/{HOOK_JS_NAME} --provider {provider} --event {event}"


def hook_entry(provider: str, event: str, timeout: int = 15, status: str | None = None) -> dict[str, Any]:
    command: dict[str, Any] = {
        "type": "command",
        "command": hook_command(provider, event),
        "timeout": timeout,
    }
    if status:
        command["statusMessage"] = status
    return command


def merge_claude(root: Path) -> None:
    path = root / ".claude" / "settings.json"
    settings = load_json(path)
    hooks = settings.setdefault("hooks", {})

    for event, config in CLAUDE_EVENTS.items():
        entry: dict[str, Any] = {
            "hooks": [hook_entry("claude", event, timeout=int(config["timeout"]))],
        }
        if "matcher" in config:
            entry["matcher"] = config["matcher"]

        existing = hooks.setdefault(event, [])
        command = entry["hooks"][0]["command"]
        if not any(
            any(hook.get("command") == command for hook in item.get("hooks", []))
            for item in existing
            if isinstance(item, dict)
        ):
            existing.append(entry)

    write_json(path, settings)


def merge_codex(root: Path) -> None:
    path = root / ".codex" / "hooks.json"
    settings = load_json(path)
    hooks = settings.setdefault("hooks", {})

    entries = {
        "SessionStart": hook_entry(
            "codex",
            "SessionStart",
            timeout=30,
            status="Loading compacted Reservoir context...",
        ),
        "PreToolUse": hook_entry(
            "codex",
            "PreToolUse",
            timeout=15,
            status="Refreshing compacted Reservoir context...",
        ),
        "PostToolUse": hook_entry(
            "codex",
            "PostToolUse",
            timeout=15,
            status="Compacting tool output context...",
        ),
    }

    for event, command in entries.items():
        entry = {"matcher": ".*", "hooks": [command]}
        existing = hooks.setdefault(event, [])
        if not any(
            any(hook.get("command") == command["command"] for hook in item.get("hooks", []))
            for item in existing
            if isinstance(item, dict)
        ):
            existing.append(entry)

    write_json(path, settings)


def merge_copilot(root: Path) -> None:
    path = root / ".github" / "hooks" / "hooks.json"
    settings = load_json(path)
    settings.setdefault("version", 1)
    hooks = settings.setdefault("hooks", {})

    entries = {
        "sessionStart": ("sessionStart", 30, "Pre-fetch compacted Reservoir context at session start"),
        "preToolUse": ("preToolUse", 15, "Refresh compacted Reservoir context before tool execution"),
        "postToolUse": ("postToolUse", 15, "Record compacted tool context for Copilot"),
    }

    for event, (hook_event, timeout, comment) in entries.items():
        command = hook_command("copilot", hook_event)
        entry = {
            "type": "command",
            "bash": command,
            "powershell": command,
            "timeoutSec": timeout,
            "comment": comment,
        }
        existing = hooks.setdefault(event, [])
        if not any(item.get("bash") == command or item.get("powershell") == command for item in existing):
            existing.append(entry)

    write_json(path, settings)


def merge_vscode(root: Path) -> None:
    path = root / ".vscode" / "agents" / "hooks.json"
    settings = load_json(path)
    settings.setdefault("version", 1)
    hooks = settings.setdefault("hooks", {})

    entries = {
        "sessionStart": ("sessionStart", 30, "Pre-fetch compacted context at session start"),
        "preToolUse": ("preToolUse", 15, "Refresh compacted context before tool execution"),
        "postToolUse": ("postToolUse", 15, "Record compacted tool context"),
    }

    for event, (hook_event, timeout, comment) in entries.items():
        command = hook_command("vscode", hook_event)
        entry = {
            "type": "command",
            "command": command,
            "timeoutSec": timeout,
            "comment": comment,
        }
        existing = hooks.setdefault(event, [])
        if not any(item.get("command") == command for item in existing):
            existing.append(entry)

    write_json(path, settings)


def update_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    current = read_text(path) if path.exists() else ""
    additions = [
        ".venv/",
        ".npm-cache/",
        ".reservoir/compacted-context*.md",
        ".reservoir/compacted-context.json",
    ]
    lines = current.splitlines()
    changed = False
    for entry in additions:
        if entry not in lines:
            lines.append(entry)
            changed = True
    if changed:
        write_text(path, "\n".join(lines).rstrip() + "\n")


def update_copilot_instructions(root: Path) -> None:
    path = root / ".github" / "copilot-instructions.md"
    current = read_text(path) if path.exists() else ""
    block = """<!-- compacted-context-start -->
## Compacted Context Hook

This repo uses `claw-compactor` hooks to write compacted local context to
`.reservoir/compacted-context.md`. Before using `.reservoir/context-bundle.json`,
prefer the compacted context file when it exists.
<!-- compacted-context-end -->
"""
    start = "<!-- compacted-context-start -->"
    end = "<!-- compacted-context-end -->"
    if start in current and end in current:
        before = current.split(start, 1)[0].rstrip()
        after = current.split(end, 1)[1].lstrip()
        current = f"{before}\n\n{block}\n{after}".rstrip() + "\n"
    else:
        current = current.rstrip() + "\n\n" + block
    write_text(path, current)


def install_token_savings_for_provider(root: Path, provider: str) -> None:
    """Install token-savings skill to provider-specific location."""
    skill_src = Path(__file__).resolve().parents[2] / "token-savings"
    if not skill_src.exists():
        return

    skill_md = skill_src / "SKILL.md"
    skill_py = skill_src / "run.py"

    provider_destinations: dict[str, Path] = {
        "claude": root / ".claude" / "skills" / "token-savings",
        "codex": root / ".codex" / "skills" / "token-savings",
        "copilot": root / ".github" / "skills" / "token-savings",
        "vscode": root / ".vscode" / "agents" / "skills" / "token-savings",
    }

    dest = provider_destinations.get(provider)
    if not dest:
        return

    for src_file in (skill_md, skill_py):
        if src_file.exists():
            dst_file = dest / src_file.name
            if src_file.resolve() != dst_file.resolve():
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)


def install_token_savings(root: Path, providers: list[str]) -> None:
    """Install token-savings skill for specified providers."""
    for provider in providers:
        install_token_savings_for_provider(root, provider)


def detect_installed_providers(root: Path) -> list[str]:
    """Detect which providers have config in this repo."""
    providers = []
    if (root / ".claude").exists():
        providers.append("claude")
    if (root / ".codex").exists():
        providers.append("codex")
    if (root / ".github").exists():
        providers.append("copilot")
    if (root / ".vscode").exists():
        providers.append("vscode")
    return providers


def validate_provider(provider: str) -> bool:
    """Check if provider name is valid."""
    return provider in ("claude", "codex", "copilot", "vscode")


def print_help() -> None:
    """Print usage information."""
    print("Usage: python run.py [provider]")
    print("")
    print("Providers:")
    print("  claude   - Install hooks and skill for Claude Code (.claude/)")
    print("  codex    - Install hooks and skill for Codex agent (.codex/)")
    print("  copilot  - Install hooks and skill for GitHub Copilot (.github/)")
    print("  vscode   - Install hooks and skill for VSCode agent (.vscode/)")
    print("")
    print("If no provider is specified, installs for all detected providers.")
    print("If no providers are detected in the repo, an error is shown.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install claw-compactor hooks for Claude, Codex, GitHub Copilot, or VSCode",
        add_help=False,
    )
    parser.add_argument(
        "provider",
        nargs="?",
        help="Provider: claude, codex, copilot, or vscode (optional; auto-detects if omitted)",
    )
    args = parser.parse_args()

    root = repo_root()
    providers: list[str] = []

    if args.provider:
        if not validate_provider(args.provider):
            print(f"Error: Invalid provider '{args.provider}'")
            print_help()
            return 1
        providers = [args.provider]
    else:
        providers = detect_installed_providers(root)
        if not providers:
            print("Error: Autodetect failed - no provider config found in repo.")
            print("Must specify a provider explicitly.")
            print_help()
            return 1

    ensure_claw_compactor()
    copy_hook_scripts(root)

    for provider in providers:
        if provider == "claude":
            merge_claude(root)
        elif provider == "codex":
            merge_codex(root)
        elif provider == "copilot":
            merge_copilot(root)
            update_copilot_instructions(root)
        elif provider == "vscode":
            merge_vscode(root)

    update_gitignore(root)
    install_token_savings(root, providers)

    provider_list = ", ".join(providers)
    print(f"Installed claw-compactor hooks for {provider_list} in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
