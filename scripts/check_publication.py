"""Read-only checks of every Git index blob; never prints matching secret values."""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
from pathlib import Path

SECRET_PATTERNS = {
    "groq-token": re.compile(rb"gsk_[A-Za-z0-9]{24,}"),
    "github-token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "github-fine-grained-token": re.compile(rb"github_pat_[A-Za-z0-9_]{30,}"),
    "aws-access-key": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "private-key": re.compile(
        rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
    ),
    "credential-in-url": re.compile(rb"https?://[^\s/:]+:[^\s/@]+@"),
}
PRIVATE_DIRECTORIES = {
    ".git", "venv", "env", "__pycache__", ".pytest_cache", ".ruff_cache",
    "artifacts", "outputs", "tmp", "temp", "uploads",
}
PRIVATE_SUFFIXES = {".log", ".tmp", ".bak", ".pem", ".key", ".p12", ".pfx",
                    ".pkl", ".pickle", ".db", ".sqlite", ".har", ".dmp", ".dump"}


def inspect_content(path: str, content: bytes) -> list[str]:
    """Return categories only: callers may report paths, never matching values."""
    findings = []
    parts = path.lower().split("/")
    if any(p in PRIVATE_DIRECTORIES or p.startswith(".venv") for p in parts):
        findings.append("private-directory")
    if any("backup" in p or "restore" in p or "checkpoint" in p for p in parts):
        findings.append("local-recovery-material")
    if parts[-1].startswith(".env") and path != ".env.example":
        findings.append("secret-configuration")
    if path.lower() == ".streamlit/secrets.toml":
        findings.append("secret-configuration")
    if path.startswith("data/") and path != "data/demo/vendas_demo.csv":
        findings.append("unapproved-data")
    if Path(path).suffix.lower() in PRIVATE_SUFFIXES:
        findings.append("private-file-type")
    if len(content) > 2_000_000:
        findings.append("oversized-file")
    if b"\x00" in content:
        findings.append("unreviewed-binary")
    findings.extend(name for name, pattern in SECRET_PATTERNS.items() if pattern.search(content))
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        findings.append("non-utf8-file")
    else:
        if path.endswith(".py"):
            try:
                compile(ast.parse(text, filename=path), path, "exec", dont_inherit=True)
            except SyntaxError:
                findings.append("python-syntax-error")
    return findings


def git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], input=input_bytes,
        check=True, capture_output=True,
    ).stdout


def check_index(root: Path) -> dict:
    records = git(root, "ls-files", "--stage", "-z").split(b"\0")
    entries = []
    for record in filter(None, records):
        header, path_bytes = record.split(b"\t", 1)
        mode, sha, stage = header.split()
        entries.append((path_bytes.decode("utf-8"), mode, sha, stage))
    if not entries:
        raise ValueError("Index is empty")
    payload = b"\n".join(e[2] for e in entries) + b"\n"
    stream = io.BytesIO(git(root, "cat-file", "--batch", input_bytes=payload))
    findings = []
    total = 0
    for path, mode, sha, stage in entries:
        header = stream.readline().split()
        if len(header) != 3 or header[0] != sha or header[1] != b"blob":
            raise ValueError("Unexpected Git object")
        size = int(header[2])
        content = stream.read(size)
        if len(content) != size or stream.read(1) != b"\n":
            raise ValueError("Truncated Git object")
        total += size
        categories = inspect_content(path, content)
        if mode not in (b"100644", b"100755") or stage != b"0":
            categories.append("unsupported-mode-or-unmerged-index")
        if categories:
            findings.append({"path": path, "categories": categories})
    ignored = git(
        root, "-c", "core.quotePath=false", "ls-files", "-ci", "--exclude-standard", "-z"
    )
    for path in filter(None, ignored.split(b"\0")):
        findings.append({"path": path.decode("utf-8"), "categories": ["tracked-but-ignored"]})
    return {
        "status": "PASS" if not findings else "BLOCKED",
        "index_files": len(entries), "index_bytes": total,
        "findings": findings,
        "scope": "Full index blobs and Python syntax; heuristic scan, not a history cleanup or CVE audit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = check_index(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
