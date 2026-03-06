# skill.json

Version 1.0.0

A universal package metadata format for AI agent skills.

`skill.json` sits at the root of a skill package and tells any package manager what's inside — which skills exist, where to find them, how to verify them, and enough metadata to make them searchable. It's designed to work with every skill package manager in the ecosystem rather than locking into any single one.

## The Problem

The AI agent skills ecosystem has half a dozen package managers and no agreed-upon way for a skill package to describe itself. Each tool reinvents discovery: some scan for `SKILL.md` files, some expect a proprietary manifest, some only support GitHub. If you publish a skill today, it works with one or two tools at best.

`skill.json` is the publisher-side answer. You describe your package once, and any service that can read JSON can consume it.

## What It Is (and Isn't)

**It is** publisher-side metadata. "Here's what's in this package."

**It is not** a consumer manifest. It doesn't say "my project needs these skills" — that's what tools like skmr's `skill.json` or skills-supply's `agents.toml` do on the consumer side.

**It is not** an agent targeting file. It doesn't say "install to Claude Code and Cursor" — that's the installer's job. It only declares compatibility *constraints* (e.g. "this skill requires Claude Code 1.2+") when they genuinely exist.

## Quick Start

Add a `skill.json` to the root of your skill repo:

```json
{
  "$schema": "https://skill.json.org/schema/1.0.0/skill.schema.json",
  "name": "my-skills",
  "version": "1.0.0",
  "description": "A collection of useful agent skills",
  "skills": [
    {
      "name": "my-skill",
      "path": "./my-skill",
      "description": "What this skill does and when an agent should use it"
    }
  ]
}
```

That's the minimum. Three required fields at the package level (`name`, `version`, `description`) and three per skill (`name`, `path`, `description`).

## Full Example

A realistic multi-skill package with all the trimmings:

```json
{
  "$schema": "https://skill.json.org/schema/1.0.0/skill.schema.json",
  "name": "document-skills",
  "version": "2.1.0",
  "description": "Document creation and manipulation skills for AI agents",
  "author": {
    "name": "Acme Corp",
    "url": "https://acme.dev"
  },
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/acme/document-skills.git"
  },
  "keywords": ["documents", "office", "files"],
  "skills": [
    {
      "name": "pdf",
      "path": "./pdf",
      "description": "Read, create, merge, split, and OCR PDF files",
      "integrity": "sha256-yY1jg1cPGoisxK/ed7yMxPeDkU8UL7pHhPAqIci0wRA=",
      "category": "documents",
      "tags": ["pdf", "ocr", "merge"],
      "requires": {
        "tools": ["python3"]
      }
    },
    {
      "name": "docx",
      "path": "./docx",
      "description": "Create and edit Word documents with formatting and templates",
      "integrity": "sha256-9kPpBqwxmqZqndp8cDTjgxYBhMLrpM6qW4a0VuFip6M=",
      "category": "documents",
      "tags": ["word", "docx", "report"],
      "requires": {
        "tools": ["python3"]
      }
    }
  ]
}
```

## Schema Overview

### Package Level

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Lowercase identifier, hyphens allowed |
| `version` | Yes | Semver |
| `description` | Yes | One-line summary |
| `author` | No | `{ name, url, email }` or npm shorthand `"Name <email> (url)"` |
| `license` | No | SPDX identifier. Inherited by skills unless overridden |
| `repository` | No | `{ type, url, directory }` or URL string shorthand |
| `homepage` | No | Documentation URL |
| `keywords` | No | Package-level search terms |
| `skills` | Yes | Array of skill entries (minimum 1) |

### Per Skill

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Matches directory name, lowercase with hyphens |
| `path` | Yes | Relative path from skill.json (`"."` for root-level) |
| `description` | Yes | What it does and when to use it |
| `version` | No | Override of package version |
| `integrity` | No | SRI hash for verification |
| `entrypoint` | No | Defaults to `SKILL.md` |
| `category` | No | Primary category for filtering |
| `tags` | No | Search terms |
| `license` | No | Override of package license |
| `author` | No | Override of package author |
| `dependencies` | No | Other skills *in this package* that must co-install |
| `requires` | No | Compatibility constraints (see below) |

### Requires

| Field | Description |
|-------|-------------|
| `min_agent_versions` | `{ "claude-code": "1.2.0" }` — agent version floor |
| `tools` | `["python3", "node"]` — runtime tools needed |
| `skills` | `["other-package/skill-name"]` — cross-package dependencies |

The full spec with design rationale lives in [`references/schema-spec.md`](references/schema-spec.md). The formal JSON Schema is at [`references/skill.schema.json`](references/skill.schema.json).

## Tooling

### Validate a skill.json

```bash
python3 scripts/validate.py skill.json
```

Add `--check-paths` to verify each skill's directory and SKILL.md exist, `--check-integrity` to verify hashes match, or `--strict` for both:

```bash
python3 scripts/validate.py skill.json --strict
```

JSON output for CI:

```bash
python3 scripts/validate.py skill.json --strict --json
```

### Compute Integrity Hashes

Hash a single skill directory:

```bash
python3 scripts/compute_integrity.py ./my-skill
# my-skill: sha256-K7gNU3sdo+OL0wNhqoVWhr3g6s1xYv72ol/pe/Unols=
```

Hash every skill under a root directory:

```bash
python3 scripts/compute_integrity.py --all . --json
```

The integrity field uses W3C Subresource Integrity format (`sha256-{base64}`). The hash covers every file in the skill directory — it changes when anything is added, removed, or modified. Package managers can use it for cache-based deduplication and tamper detection.

### AI Agent Skill

This project also ships as an AI agent skill. Install the `skill-json-generator` skill into Claude Code, Cursor, or any agent that supports skills, and it can generate `skill.json` files for your projects by scanning for SKILL.md files, inferring metadata from git and frontmatter, and producing a validated output.

## Package Manager Compatibility

`skill.json` is designed so that every existing tool can read the fields it cares about and ignore the rest.

| Tool | Reads | Notes |
|------|-------|-------|
| [Automatic](https://github.com/velvet-tiger/automatic) | Full compatibility ||


## Common Patterns

**Single skill at repo root** — Set `"path": "."` when the repo *is* the skill.

**Monorepo** — Use `repository.directory` to indicate where skill.json lives within a larger repo. Paths within `skills[]` are still relative to skill.json itself.

**Skill dependencies** — Use `dependencies` for intra-package relationships (skill B requires skill A from the same package). Use `requires.skills` for cross-package dependencies (`"other-package/skill-name"` format).

**Runtime tools** — Declare `requires.tools` when a skill genuinely needs something like Python or Node installed. Don't declare agent targets here — that's an installer concern.

## Design Decisions

**JSON, not TOML or YAML.** Every tool in the ecosystem except skills-supply already uses JSON. JSON Schema validation is mature. YAML has the Norway problem. TOML is fine but adds a dependency for the sake of it.

**Publisher-side only.** Mixing "what's in this package" with "what does my project need" creates a format that serves neither purpose well. Consumer manifests are a different file with different semantics.

**No agent targeting.** A skill that works with Claude Code today will probably work with Cursor tomorrow. Declaring install targets in the package metadata bakes in assumptions about which agents exist and creates churn. The `requires.min_agent_versions` field handles genuine compatibility constraints without dictating targets.

**Integrity from day one.** SRI format is a W3C standard already used by npm and browsers. Self-describing (`sha256-...`) so it's forward-compatible with future hash algorithms. Optional, so it doesn't block adoption, but present so tooling can rely on it.

**Explicit paths.** `path` is required even though it could theoretically be inferred from `name`, because packages use every conceivable directory structure (`./skills/pdf`, `./pdf`, `./src/skills/pdf`). Explicit beats implicit.

## Project Structure

```
skill-json-generator/
├── SKILL.md                          # Agent skill instructions
├── skill.json                        # This package's own metadata (dogfooded)
├── README.md
├── references/
│   ├── schema-spec.md                # Full specification
│   └── skill.schema.json             # JSON Schema for validation
└── scripts/
    ├── compute_integrity.py          # SRI hash computation
    └── validate.py                   # Schema + path + integrity validation
```

## Requirements

Python 3.10+ for the scripts. The `jsonschema` package is needed for validation:

```bash
pip install jsonschema
```

No other dependencies. The scripts are deliberately standalone.

## License

MIT

## Author

skill.json was created by [Christopher Skene](https://github.com/xtfer)
