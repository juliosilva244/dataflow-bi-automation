"""Lista arquivos candidatos respeitando o .gitignore, sem inicializar Git."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path


def load_patterns(root: Path) -> list[str]:
    return [
        line.strip()
        for line in (root / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def is_ignored(relative: str, patterns: list[str]) -> bool:
    """Avalia o subconjunto de padrões usado pelo .gitignore deste projeto."""
    ignored = False
    parts = relative.split("/")
    for raw_pattern in patterns:
        negated = raw_pattern.startswith("!")
        pattern = raw_pattern[1:] if negated else raw_pattern
        pattern = pattern.lstrip("/")
        directory_pattern = pattern.endswith("/")
        pattern = pattern.rstrip("/")
        if not pattern:
            continue

        if "/" in pattern:
            matched = fnmatch.fnmatchcase(relative, pattern) or (
                directory_pattern and relative.startswith(pattern + "/")
            )
        else:
            matched = any(fnmatch.fnmatchcase(part, pattern) for part in parts)

        if matched:
            ignored = not negated
    return ignored


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    patterns = load_patterns(root)
    candidates: list[str] = []
    for current_root, directory_names, file_names in os.walk(root, topdown=True):
        current = Path(current_root)
        relative_root = current.relative_to(root)
        directory_names[:] = [
            name
            for name in directory_names
            if not is_ignored((relative_root / name).as_posix() + "/", patterns)
        ]
        for name in file_names:
            relative = (relative_root / name).as_posix()
            if not is_ignored(relative, patterns):
                candidates.append(relative)

    for relative in sorted(candidates):
        print(relative)


if __name__ == "__main__":
    main()
