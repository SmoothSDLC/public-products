#!/usr/bin/env python3
"""
Script: validate-skill.py
Requires: python 3.8+
Purpose: Validates that the install-claw-compactor skill conforms to .github/skills.instructions.md
Idempotent: yes
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows (emoji check/cross marks)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_NAME = SKILL_DIR.name
SKILL_MD = SKILL_DIR / "SKILL.md"
MAX_SKILL_LINES = 500

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ✅ {label}")
    else:
        print(f"  ❌ {label}")
        failures.append(label)


print(f"\n{'=' * 60}")
print(f"  Skill Self-Validation: {SKILL_NAME}")
print(f"{'=' * 60}\n")

# 1. Required files exist
check(SKILL_MD.exists(), "SKILL.md exists")
check((SKILL_DIR / "scripts" / "validate-skill.py").exists(), "scripts/validate-skill.py exists")
check((SKILL_DIR / "scripts" / "run.py").exists(), "scripts/run.py exists")

# 2. Asset files exist (hook templates bundled with skill)
check((SKILL_DIR / "assets" / "compact-context.py").exists(), "assets/compact-context.py exists")
check((SKILL_DIR / "assets" / "compact-context.js").exists(), "assets/compact-context.js exists")

# 3. SKILL.md quality checks
if SKILL_MD.exists():
    lines = SKILL_MD.read_text(encoding="utf-8").splitlines()
    check(len(lines) <= MAX_SKILL_LINES, f"SKILL.md under {MAX_SKILL_LINES} lines (actual: {len(lines)})")

    full_text = "\n".join(lines)

    # name matches directory
    for line in lines:
        if line.startswith("name:"):
            declared = line.split(":", 1)[1].strip()
            check(declared == SKILL_NAME, f"SKILL.md name '{declared}' matches directory '{SKILL_NAME}'")
            break

    # description starts with "Use this skill when"
    desc_match = re.search(r"description:\s*>\s*\n\s*(.*)", full_text)
    if desc_match:
        first_desc_line = desc_match.group(1).strip()
        check(
            first_desc_line.startswith("Use this skill when"),
            f"description starts with 'Use this skill when' (found: '{first_desc_line[:50]}...')",
        )
    else:
        check(False, "description field found in frontmatter")

    # required sections
    for section in ("## Purpose", "## Prerequisites", "## Workflow", "## Gotchas"):
        check(section in full_text, f"Required section present: {section}")

    # referenced files exist
    refs = re.findall(r"`(scripts/[\w\-\.]+|assets/[\w\-\.]+|references/[\w\-\.]+)`", full_text)
    for ref in set(refs):
        check((SKILL_DIR / ref).exists(), f"Referenced file exists: {ref}")

# 4. eval_queries.json
eval_json = SKILL_DIR / "scripts" / "eval_queries.json"
if eval_json.exists():
    queries = json.loads(eval_json.read_text(encoding="utf-8"))
    should_trigger = [q for q in queries if q.get("should_trigger")]
    should_not = [q for q in queries if not q.get("should_trigger")]
    check(len(queries) >= 10, f"eval_queries.json has >= 10 entries (found: {len(queries)})")
    check(len(should_trigger) >= 5, f"At least 5 should-trigger queries (found: {len(should_trigger)})")
    check(len(should_not) >= 5, f"At least 5 should-not queries (found: {len(should_not)})")
else:
    print("  ℹ️  scripts/eval_queries.json not found — skipping trigger eval checks")

# 5. skills-ref validate (optional — install: pip install skills-ref)
try:
    result = subprocess.run(
        ["skills-ref", "validate", str(SKILL_DIR)],
        capture_output=True,
        text=True,
    )
    check(
        result.returncode == 0,
        f"skills-ref validate passes (output: {result.stdout.strip() or result.stderr.strip()})",
    )
except FileNotFoundError:
    print("  ℹ️  skills-ref not in PATH — skipping spec validation (install: pip install skills-ref)")

# Results
print(f"\n{'=' * 60}")
if failures:
    print(f"  RESULT: FAILED ({len(failures)} issue(s))")
    for f in failures:
        print(f"    • {f}")
    print(f"{'=' * 60}\n")
    sys.exit(1)
else:
    print(f"  RESULT: PASSED")
    print(f"{'=' * 60}\n")
    sys.exit(0)
