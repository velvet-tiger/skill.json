#!/usr/bin/env python3
"""
Compute SRI-format integrity hashes for skill directories.

Usage:
    python3 compute_integrity.py <skill-directory> [<skill-directory> ...]
    python3 compute_integrity.py --all <root-directory>

Output:
    Prints skill-name: integrity-hash pairs, one per line.
    Use --json to output as a JSON object for programmatic use.

Algorithm:
    1. List all files in the skill directory recursively, sorted lexicographically
    2. For each file, compute SHA-256 of its contents
    3. Concatenate all "relative-path:sha256-hex\n" pairs into a single string
    4. SHA-256 hash that concatenated string
    5. Base64-encode and prefix with "sha256-"
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a single file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_directory_integrity(skill_dir: Path) -> str:
    """
    Compute SRI integrity hash for an entire skill directory.

    Returns an SRI-format string like "sha256-K7gNU3sdo+OL0w...".
    """
    skill_dir = skill_dir.resolve()

    if not skill_dir.is_dir():
        raise ValueError(f"Not a directory: {skill_dir}")

    # Collect all files, sorted lexicographically by relative path
    file_entries: list[str] = []

    for root, _dirs, files in os.walk(skill_dir):
        for filename in files:
            filepath = Path(root) / filename
            rel_path = filepath.relative_to(skill_dir).as_posix()

            # Skip hidden files and common non-content files
            if any(part.startswith(".") for part in rel_path.split("/")):
                continue

            # Skip the package manifest itself to avoid circular integrity references
            if rel_path == "skills.json":
                continue

            file_hash = compute_file_hash(filepath)
            file_entries.append(f"{rel_path}:{file_hash}")

    file_entries.sort()

    # Concatenate and hash
    manifest_content = "\n".join(file_entries) + "\n"
    overall_hash = hashlib.sha256(manifest_content.encode("utf-8")).digest()

    # Base64 encode for SRI format
    b64_hash = base64.b64encode(overall_hash).decode("ascii")

    return f"sha256-{b64_hash}"


def find_skill_dirs(root: Path) -> list[Path]:
    """Find all directories containing a SKILL.md file."""
    skill_dirs: list[Path] = []
    for skill_md in root.rglob("SKILL.md"):
        skill_dirs.append(skill_md.parent)
    return sorted(skill_dirs)


def get_skill_name(skill_dir: Path) -> str:
    """Extract skill name from SKILL.md frontmatter or fall back to directory name."""
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        with open(skill_md, "r", encoding="utf-8") as f:
            in_frontmatter = False
            for line in f:
                line = line.strip()
                if line == "---":
                    if in_frontmatter:
                        break
                    in_frontmatter = True
                    continue
                if in_frontmatter and line.startswith("name:"):
                    return line.split(":", 1)[1].strip().strip("\"'")
    return skill_dir.name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute SRI integrity hashes for skill directories"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Skill directories to hash (or root directory with --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Find all SKILL.md files under the given directory and hash each",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output as JSON object",
    )

    args = parser.parse_args()

    if not args.paths:
        parser.print_help()
        sys.exit(1)

    results: dict[str, str] = {}

    for path_str in args.paths:
        path = Path(path_str)

        if args.all:
            skill_dirs = find_skill_dirs(path)
            if not skill_dirs:
                print(f"No SKILL.md files found under {path}", file=sys.stderr)
                continue
            for skill_dir in skill_dirs:
                name = get_skill_name(skill_dir)
                integrity = compute_directory_integrity(skill_dir)
                results[name] = integrity
        else:
            if not path.is_dir():
                print(f"Not a directory: {path}", file=sys.stderr)
                sys.exit(1)
            name = get_skill_name(path)
            integrity = compute_directory_integrity(path)
            results[name] = integrity

    if args.output_json:
        print(json.dumps(results, indent=2))
    else:
        for name, integrity in results.items():
            print(f"{name}: {integrity}")


if __name__ == "__main__":
    main()
