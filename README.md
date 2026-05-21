# SmoothSDLC Public Skills

Welcome to SmoothSDLC's public skills repository. This collection contains AI agent automation tools designed to enhance productivity and reduce operational friction across development workflows.

## About SmoothSDLC

SmoothSDLC delivers fixed-scope DevOps and Azure cloud automation services, focusing on CI/CD pipelines, Infrastructure-as-Code, and operational automation. Our core mission is to build production-ready solutions that remain maintainable and coherent long after handoff—ensuring future changes stay cheaper and safer to implement. This repository extends that philosophy into the AI agent ecosystem.

---

## Published Skills

### [install-claw-compactor](./skills/install-claw-compactor/)

The `install-claw-compactor` skill automates the setup of context-compaction hooks for Claude Code, GitHub Copilot, Codex, and VSCode agents. It wraps the open-source `claw-compactor` tool and makes it accessible outside of the open-claw platform, eliminating the need for complex manual configuration. The installer sets up agent hooks that automatically compact conversation context at key lifecycle moments (SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolBatch) to keep responses fast and within token limits. Compaction output is written to `.reservoir/compacted-context.md` where agents read it instead of the full context bundle. The skill also installs the companion `token-savings` skill for each provider, making token compression visible and measurable—so you can track exactly how much context you're saving through compaction. The installer is idempotent and runs on Windows, macOS, and Linux.

---

## Quick Start

### Using install-claw-compactor

1. Navigate to your repository root (the directory containing `.git/`):
   ```bash
   cd /path/to/your/repo
   ```

2. Copy the skill into your repository:
   ```bash
   mkdir -p .agent/skills
   cp -r install-claw-compactor .agent/skills/
   ```

3. Run the installer (auto-detects providers):
   ```bash
   python .agent/skills/install-claw-compactor/scripts/run.py
   ```

   Or install for a specific provider:
   ```bash
   python .agent/skills/install-claw-compactor/scripts/run.py claude    # Claude Code
   python .agent/skills/install-claw-compactor/scripts/run.py copilot   # GitHub Copilot
   python .agent/skills/install-claw-compactor/scripts/run.py codex     # Codex
   python .agent/skills/install-claw-compactor/scripts/run.py vscode    # VSCode
   ```

4. Validate the installation:
   ```bash
   python .agent/skills/install-claw-compactor/scripts/validate-skill.py
   ```

---

## Requirements

- **Python 3.8+** (available as `python`, `python3`, or `py` in PATH)
- **Node.js** (available as `node` in PATH)
- **pip** (the hook auto-installs `claw-compactor` on first use if missing)
- Repository with `.git/` directory

---

## License

Proprietary. For more information, visit [SmoothSDLC](https://smoothsdlc.com).

---

## Support

For issues, questions, or contributions, please reach out to the SmoothSDLC team.
