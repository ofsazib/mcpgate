#!/usr/bin/env python3
"""Automated release: decide semver bump from conventional commits, tag, push.

Usage:
    uv run python scripts/release.py            # dry-run: show plan only
    uv run python scripts/release.py --yes      # execute: checks, bump, tag, push

Bump rules (commits since last tag):
- any `feat!:`/`fix!:` or a `BREAKING CHANGE:` footer  -> major
- else any `feat:`                                     -> minor
- else (fix:, docs:, chore:, ...)                      -> patch
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT = ROOT / "src" / "mcpgate" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"

SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def run(*cmd: str, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{result.stdout}{result.stderr}")
    return result.stdout.strip()


def current_version() -> tuple[int, int, int]:
    text = run("git", "describe", "--tags", "--abbrev=0", check=False)
    m = SEMVER.match(text) if text else None
    if m:
        return int(m[1]), int(m[2]), int(m[3])
    m = re.search(r'^version = "(\d+)\.(\d+)\.(\d+)"', PYPROJECT.read_text(), re.M)
    if not m:
        sys.exit("no version found: no tags and no version in pyproject.toml")
    return int(m[1]), int(m[2]), int(m[3])


def commits_since(tag: str | None) -> list[str]:
    rng = f"{tag}..HEAD" if tag else "HEAD"
    log = run("git", "log", "--no-merges", "--format=%s%n%b%x00", rng)
    return [c.strip() for c in log.split("\0") if c.strip()]


def decide_bump(commits: list[str]) -> str:
    for c in commits:
        if re.search(r"^\w+(\(\w+\))?!:", c, re.M) or "BREAKING CHANGE:" in c:
            return "major"
    if any(c.startswith("feat") for c in commits):
        return "minor"
    return "patch"


def bump(version: tuple[int, int, int], kind: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if kind == "major":
        return major + 1, 0, 0
    if kind == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def update_changelog(new: str, commits: list[str]) -> None:
    today = datetime.date.today().isoformat()
    groups: dict[str, list[str]] = {"Added": [], "Fixed": [], "Changed": [], "Other": []}
    for c in commits:
        subject = c.splitlines()[0]
        if subject.startswith("feat"):
            groups["Added"].append(subject)
        elif subject.startswith("fix"):
            groups["Fixed"].append(subject)
        elif subject.startswith(("docs", "refactor", "perf")):
            groups["Changed"].append(subject)
        else:
            groups["Other"].append(subject)

    lines = [f"## [{new}] - {today}", ""]
    for name, header in (
        ("Added", "### Added"),
        ("Fixed", "### Fixed"),
        ("Changed", "### Changed"),
        ("Other", "### Other"),
    ):
        if groups[name]:
            lines.append(header)
            lines += [f"- {s}" for s in groups[name]]
            lines.append("")
    text = CHANGELOG.read_text()
    marker = "## [0.1.0] - 2026-09-02"
    CHANGELOG.write_text(text.replace(marker, "\n".join(lines) + "\n" + marker, 1))


def set_version(new: str) -> None:
    py = PYPROJECT.read_text()
    PYPROJECT.write_text(
        re.sub(r'^version = "[^"]+"', f'version = "{new}"', py, count=1, flags=re.M)
    )
    init = INIT.read_text()
    INIT.write_text(re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new}"', init, count=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="execute the release (default: dry-run)")
    args = ap.parse_args()

    if run("git", "status", "--porcelain"):
        sys.exit("working tree not clean — commit or stash first")
    if run("git", "branch", "--show-current") != "main":
        sys.exit("must release from main")

    tag = run("git", "describe", "--tags", "--abbrev=0", check=False) or None
    commits = commits_since(tag)
    if not commits:
        sys.exit("no commits since last tag — nothing to release")
    if not any(c.startswith(("feat", "fix", "perf")) for c in commits):
        print("no releasable commits (feat/fix) since last tag — skipping")
        return

    kind = decide_bump(commits)
    old = current_version()
    if tag is None:
        kind, new = "initial", "{}.{}.{}".format(*old)
    else:
        new = "{}.{}.{}".format(*bump(old, kind))

    print(f"last tag:    {tag or '(none)'}")
    print(f"commits:     {len(commits)}")
    print(f"bump:        {kind}  {old} -> {new}")
    print("\nchangelog entries:")
    for c in commits:
        print(f"  {c.splitlines()[0]}")

    if not args.yes:
        print("\ndry-run only. run with --yes to release.")
        return

    print("\nrunning checks (pytest, ruff, mypy)...")
    for cmd in (
        ["uv", "run", "coverage", "run", "-m", "pytest"],
        ["uv", "run", "coverage", "report"],
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "mypy", "src"],
    ):
        run(*cmd)
        print(f"  ok: {' '.join(cmd[-2:])}")

    set_version(new)
    update_changelog(new, commits)
    run("git", "add", "pyproject.toml", "src/mcpgate/__init__.py", "CHANGELOG.md")
    run("git", "commit", "-m", f"chore(release): v{new}")
    run("git", "tag", f"v{new}")
    run("git", "push", "origin", "main")
    run("git", "push", "origin", f"v{new}")
    print(f"\nreleased v{new} — release.yml will build and publish to PyPI.")
    print("track it: https://github.com/ofsazib/mcpgate/actions/workflows/release.yml")


if __name__ == "__main__":
    main()
