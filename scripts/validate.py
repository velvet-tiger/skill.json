#!/usr/bin/env python3
"""
Validate a skills.json file against the JSON Schema.

Usage:
    python3 validate.py <skills.json>
    python3 validate.py <skills.json> --schema <custom-schema.json>
    python3 validate.py <skills.json> --check-paths
    python3 validate.py <skills.json> --check-integrity

Options:
    --schema        Path to a custom JSON Schema file (defaults to bundled schema)
    --check-paths   Verify that each skill's path exists and contains a SKILL.md
    --check-integrity  Verify integrity hashes match actual directory contents
    --strict        Enable all checks (paths + integrity)
    --json          Output results as JSON
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    print(
        "jsonschema not installed. Run: pip install jsonschema --break-system-packages",
        file=sys.stderr,
    )
    sys.exit(1)


def load_bundled_schema() -> dict[str, Any]:
    """Load the JSON Schema bundled with this skill."""
    schema_path = Path(__file__).parent.parent / "references" / "skills.schema.json"
    if not schema_path.exists():
        print(f"Bundled schema not found at {schema_path}", file=sys.stderr)
        sys.exit(1)
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate data against JSON Schema. Returns list of error messages."""
    errors: list[str] = []
    validator = jsonschema.Draft7Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  {path}: {error.message}")
    return errors


def check_paths(data: dict[str, Any], base_dir: Path) -> list[str]:
    """Verify that skill paths exist and contain SKILL.md."""
    errors: list[str] = []
    for i, skill in enumerate(data.get("skills", [])):
        skill_path = skill.get("path", "")
        skill_name = skill.get("name", f"skills[{i}]")
        full_path = (base_dir / skill_path).resolve()

        if not full_path.is_dir():
            errors.append(f"  {skill_name}: path '{skill_path}' is not a directory")
            continue

        entrypoint = skill.get("entrypoint", "SKILL.md")
        entrypoint_path = full_path / entrypoint
        if not entrypoint_path.is_file():
            errors.append(
                f"  {skill_name}: entrypoint '{entrypoint}' not found in '{skill_path}'"
            )

    return errors


def check_integrity(data: dict[str, Any], base_dir: Path) -> list[str]:
    """Verify integrity hashes match directory contents."""
    errors: list[str] = []

    # Import compute function from sibling script
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from compute_integrity import compute_directory_integrity
    except ImportError:
        return ["  Cannot import compute_integrity module"]

    for i, skill in enumerate(data.get("skills", [])):
        integrity = skill.get("integrity")
        if not integrity:
            continue

        skill_path = skill.get("path", "")
        skill_name = skill.get("name", f"skills[{i}]")
        full_path = (base_dir / skill_path).resolve()

        if not full_path.is_dir():
            continue  # Path check handles this

        actual = compute_directory_integrity(full_path)
        if actual != integrity:
            errors.append(
                f"  {skill_name}: integrity mismatch\n"
                f"    expected: {integrity}\n"
                f"    actual:   {actual}"
            )

    return errors


def check_internal_consistency(data: dict[str, Any]) -> list[str]:
    """Check for internal consistency issues."""
    errors: list[str] = []
    skill_names = [s.get("name") for s in data.get("skills", [])]

    # Check for duplicate skill names
    seen: set[str] = set()
    for name in skill_names:
        if name in seen:
            errors.append(f"  Duplicate skill name: '{name}'")
        seen.add(name)

    # Check dependency references
    for skill in data.get("skills", []):
        for dep in skill.get("dependencies", []):
            if dep not in skill_names:
                errors.append(
                    f"  {skill.get('name')}: dependency '{dep}' not found in this package"
                )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a skills.json file")
    parser.add_argument("file", help="Path to skills.json")
    parser.add_argument("--schema", help="Path to custom JSON Schema file")
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Verify skill paths exist with SKILL.md",
    )
    parser.add_argument(
        "--check-integrity",
        action="store_true",
        help="Verify integrity hashes match",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable all checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output as JSON",
    )

    args = parser.parse_args()

    if args.strict:
        args.check_paths = True
        args.check_integrity = True

    # Load files
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    schema = (
        json.loads(Path(args.schema).read_text())
        if args.schema
        else load_bundled_schema()
    )

    base_dir = file_path.parent

    # Run checks
    results: dict[str, list[str]] = {}

    schema_errors = validate_schema(data, schema)
    if schema_errors:
        results["schema"] = schema_errors

    consistency_errors = check_internal_consistency(data)
    if consistency_errors:
        results["consistency"] = consistency_errors

    if args.check_paths:
        path_errors = check_paths(data, base_dir)
        if path_errors:
            results["paths"] = path_errors

    if args.check_integrity:
        integrity_errors = check_integrity(data, base_dir)
        if integrity_errors:
            results["integrity"] = integrity_errors

    # Output
    if args.output_json:
        output = {
            "valid": len(results) == 0,
            "file": str(file_path),
            "errors": results,
        }
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f"✅ {file_path} is valid")
        else:
            print(f"❌ {file_path} has errors:\n")
            for category, errors in results.items():
                print(f"[{category}]")
                for error in errors:
                    print(error)
                print()

    sys.exit(0 if not results else 1)


if __name__ == "__main__":
    main()
