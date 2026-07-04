#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")
MAC_USER_PREFIX = "/" + "Users" + "/"


def read_lock(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value
    return values


def scan_text_files(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        try:
            lines = path.read_text().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(lines, 1):
            if MAC_USER_PREFIX in line:
                findings.append(f"{path}:{number}: contains a macOS user path")
            if KEY_PATTERN.search(line):
                findings.append(f"{path}:{number}: contains a possible API key")
    return findings


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT
    ).decode()
    return [ROOT / name for name in output.split("\0") if name]


def main() -> int:
    findings = scan_text_files(tracked_files())
    required = [
        ROOT / "README.md",
        ROOT / "docs/ARCHITECTURE.md",
        ROOT / "docs/AI_COLLABORATION.md",
        ROOT / "docs/RECORDING.md",
        ROOT / ".env.example",
    ]
    findings.extend(f"{path}: missing required release file" for path in required if not path.is_file())

    lock = read_lock(ROOT / "config/hermes-source.lock")
    if not re.fullmatch(r"[0-9a-f]{40}", lock.get("commit", "")):
        findings.append("config/hermes-source.lock: missing immutable commit")

    if findings:
        print("Release check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print(f"Release check passed: {len(tracked_files())} public files scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
