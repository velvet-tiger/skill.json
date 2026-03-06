# skill.json Specification

**Version:** 1.0.0-draft
**Purpose:** Publisher-side package metadata for AI agent skill packages

## Overview

`skill.json` lives at the root of a skill package (a repository, directory, or archive containing one or more AI agent skills). It tells any package manager what skills exist in this package, where to find them, and enough metadata to index, search, verify, and install them.

It does **not** declare which agents to install to, or which skills a consumer project needs. Those are consumer-side concerns handled by installer tools (skmr, skillman, skillbox, skills-supply, etc.).

### Design Principles

1. **Publisher-side only** — Describes what's here, not what's needed elsewhere
2. **Source-agnostic** — No opinion on where the package is hosted (GitHub, GitLab, local, registry, HTTP)
3. **Agent-neutral** — Agent targeting is the installer's job; we only declare compatibility constraints
4. **One format, any size** — Same structure whether the package has 1 skill or 50
5. **Integrity from day one** — Content hashes for verification and caching
6. **Registry-friendly** — Enough metadata for any registry or search index to consume without reading SKILL.md files

### Relationship to SKILL.md

Each skill folder already contains a `SKILL.md` with YAML frontmatter (`name`, `description`, optional `license`). `skill.json` does **not** replace this — it wraps it with package-level context and enriches per-skill metadata for tooling that shouldn't need to parse markdown frontmatter.

If `skill.json` and SKILL.md frontmatter conflict, `skill.json` is authoritative for tooling purposes. SKILL.md remains authoritative for the agent at runtime.

## File Location

```
my-skill-package/
├── skill.json               ← this file
├── frontend-design/
│   ├── SKILL.md
│   └── references/
├── pdf/
│   ├── SKILL.md
│   └── scripts/
└── LICENSE
```

## Schema

### Top-Level (Package)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | `string` | No | URL to the JSON Schema for validation |
| `name` | `string` | **Yes** | Package identifier. Lowercase, hyphens allowed. e.g. `"anthropic-document-skills"` |
| `version` | `string` | **Yes** | Semver version of the package. e.g. `"1.2.0"` |
| `description` | `string` | **Yes** | One-line package summary |
| `author` | `Author` | No | Package author (see Author type) |
| `license` | `string` | No | SPDX identifier or `"SEE LICENSE"`. Inherited by skills unless overridden |
| `homepage` | `string` (URL) | No | Documentation or landing page URL |
| `repository` | `Repository` | No | Source repository (see Repository type) |
| `keywords` | `string[]` | No | Package-level search terms |
| `skills` | `Skill[]` | **Yes** | Array of skills in this package (minimum 1) |

### Skill

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **Yes** | Unique skill identifier within this package. Must match the directory name. Lowercase, hyphens allowed |
| `path` | `string` | **Yes** | Relative path from `skill.json` to the skill directory. e.g. `"./frontend-design"` |
| `description` | `string` | **Yes** | What this skill does and when to use it. Used by registries and search |
| `version` | `string` | No | Skill-specific version override. Defaults to package `version` |
| `integrity` | `string` | No | SRI-format hash of skill directory contents. e.g. `"sha256-abc123..."` |
| `entrypoint` | `string` | No | Main instruction file relative to `path`. Defaults to `"SKILL.md"` |
| `category` | `string` | No | Primary category (see Categories) |
| `tags` | `string[]` | No | Search/filter tags. e.g. `["react", "css", "ui"]` |
| `license` | `string` | No | SPDX identifier override for this skill |
| `author` | `Author` | No | Author override for this skill |
| `dependencies` | `string[]` | No | Names of other skills **in this package** that must also be installed |
| `requires` | `Requires` | No | Compatibility constraints (see Requires type) |

### Author

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **Yes** | Display name |
| `url` | `string` | No | Website or profile URL |
| `email` | `string` | No | Contact email |

Shorthand: `"author": "Name <email> (url)"` is also valid, following npm convention.

### Repository

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `string` | **Yes** | Repository type: `"git"`, `"mercurial"`, etc. |
| `url` | `string` | **Yes** | Clone URL. e.g. `"https://github.com/org/repo.git"` |
| `directory` | `string` | No | Subdirectory within the repo if skill.json isn't at the root |

Shorthand: `"repository": "https://github.com/org/repo"` is also valid for git repos.

### Requires

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `min_agent_versions` | `Record<string, string>` | No | Minimum agent versions keyed by agent slug. e.g. `{ "claude-code": "1.0.0" }` |
| `tools` | `string[]` | No | Required tool/runtime availability. e.g. `["python3", "node"]` |
| `skills` | `string[]` | No | External skill dependencies (other packages). Format: `"package-name/skill-name"` |

### Categories

Recommended values (not an exhaustive enum — custom values are allowed):

- `development` — Code patterns, frameworks, architecture
- `documents` — PDF, DOCX, XLSX, PPTX generation/manipulation
- `creative` — Design, art, media creation
- `business` — Sales, marketing, operations, communications
- `productivity` — Workflow automation, organisation, tooling
- `infrastructure` — DevOps, cloud, CI/CD, deployment
- `data` — Analysis, visualisation, ETL, databases
- `testing` — QA, regression, E2E, unit testing

## Integrity Hashing

The `integrity` field uses Subresource Integrity (SRI) format: `{algorithm}-{base64-hash}`.

To compute:
1. List all files in the skill directory recursively, sorted lexicographically by relative path
2. For each file, compute SHA-256 of its contents
3. Concatenate all `relative-path:sha256-hash\n` pairs into a single string
4. SHA-256 hash that concatenated string
5. Base64-encode the result

This gives a single deterministic hash for the entire skill directory that changes when any file is added, removed, or modified.

Package managers **should** verify integrity on install when the field is present. Package managers **must not** reject packages that omit integrity (it's opt-in).

## Examples

### Minimal Single-Skill Package

```json
{
  "$schema": "https://skill.json.org/schema/1.0.0/skill.schema.json",
  "name": "my-react-skill",
  "version": "0.1.0",
  "description": "React best practices for modern applications",
  "skills": [
    {
      "name": "react-best-practices",
      "path": ".",
      "description": "React patterns, hooks, and component architecture for production apps"
    }
  ]
}
```

Note: when a package contains a single skill at its root, `"path": "."` is valid.

### Multi-Skill Package (e.g. Anthropic's document skills)

```json
{
  "$schema": "https://skill.json.org/schema/1.0.0/skill.schema.json",
  "name": "anthropic-document-skills",
  "version": "2.1.0",
  "description": "Document creation and manipulation skills for Claude",
  "author": {
    "name": "Anthropic",
    "url": "https://anthropic.com"
  },
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/anthropics/skills.git"
  },
  "homepage": "https://agentskills.io",
  "keywords": ["documents", "office", "files"],
  "skills": [
    {
      "name": "pdf",
      "path": "./pdf",
      "description": "Read, create, merge, split, rotate, watermark, fill, encrypt, and OCR PDF files",
      "integrity": "sha256-K7gNU3sdo+OL0wNhqoVWhr3g6s1xYv72ol/pe/Unols=",
      "category": "documents",
      "tags": ["pdf", "ocr", "merge", "split"],
      "requires": {
        "tools": ["python3"]
      }
    },
    {
      "name": "docx",
      "path": "./docx",
      "description": "Create and edit Word documents with tables, headings, page numbers, and formatting",
      "integrity": "sha256-abc123def456ghi789jkl012mno345pqr678stu901=",
      "category": "documents",
      "tags": ["word", "docx", "report", "letter"],
      "requires": {
        "tools": ["python3"]
      }
    },
    {
      "name": "xlsx",
      "path": "./xlsx",
      "description": "Create and edit Excel spreadsheets with formulas, charts, and data analysis",
      "integrity": "sha256-xyz987wvu654tsr321qpo098nml765kji432hgf109=",
      "category": "documents",
      "tags": ["excel", "spreadsheet", "data", "charts"],
      "requires": {
        "tools": ["python3"]
      }
    },
    {
      "name": "pptx",
      "path": "./pptx",
      "description": "Create and edit PowerPoint presentations with layouts, speaker notes, and templates",
      "integrity": "sha256-ppt456abc789def012ghi345jkl678mno901pqr234=",
      "category": "documents",
      "tags": ["powerpoint", "slides", "presentation", "deck"],
      "requires": {
        "tools": ["python3"]
      }
    }
  ]
}
```

### Skill With Dependencies and Compatibility Constraints

```json
{
  "$schema": "https://skill.json.org/schema/1.0.0/skill.schema.json",
  "name": "fullstack-dev-kit",
  "version": "1.0.0",
  "description": "Full-stack development skill pack",
  "author": "Chris <chris@example.com> (https://example.com)",
  "license": "MIT",
  "repository": "https://github.com/example/fullstack-dev-kit",
  "skills": [
    {
      "name": "frontend-design",
      "path": "./skills/frontend-design",
      "description": "Production-grade UI components with distinctive design",
      "category": "development",
      "tags": ["frontend", "css", "react", "design"],
      "requires": {
        "min_agent_versions": {
          "claude-code": "1.2.0"
        }
      }
    },
    {
      "name": "backend-api",
      "path": "./skills/backend-api",
      "description": "REST and GraphQL API patterns with proper error handling",
      "category": "development",
      "tags": ["api", "rest", "graphql", "backend"]
    },
    {
      "name": "fullstack-patterns",
      "path": "./skills/fullstack-patterns",
      "description": "End-to-end patterns that bridge frontend and backend",
      "category": "development",
      "tags": ["fullstack", "architecture", "patterns"],
      "dependencies": ["frontend-design", "backend-api"]
    }
  ]
}
```

### Monorepo With Nested skill.json

In a monorepo, `skill.json` can live in a subdirectory:

```
monorepo/
├── packages/
│   └── skills/
│       ├── skill.json         ← repository.directory = "packages/skills"
│       ├── my-skill-a/
│       │   └── SKILL.md
│       └── my-skill-b/
│           └── SKILL.md
└── ...
```

```json
{
  "name": "my-org-skills",
  "version": "1.0.0",
  "description": "Internal skills for my organisation",
  "repository": {
    "type": "git",
    "url": "https://github.com/my-org/monorepo.git",
    "directory": "packages/skills"
  },
  "skills": [
    { "name": "my-skill-a", "path": "./my-skill-a", "description": "..." },
    { "name": "my-skill-b", "path": "./my-skill-b", "description": "..." }
  ]
}
```

## Compatibility Mapping

How each existing tool can consume `skill.json`:

| Tool | What it reads from skill.json |
|------|-------------------------------|
| **skmr** | `skills[].name` to populate its manifest entries |
| **skillman** | `skills[].name` to populate `{ source, skills: [...] }` |
| **skillbox** | `skills[].name` + `skills[].path` for install targeting |
| **skills-manifest** | `skills[].name` for the `skills: { "repo": { "name": true } }` map |
| **skills-supply (sk)** | `skills[].name` + `skills[].path` for skill discovery (alternative to scanning for SKILL.md) |
| **skills-detector** | `skills[].tags` + `skills[].category` + `skills[].description` for matching |
| **MCP Registry** | `name` (namespace), `version`, `description`, `repository` for registry entries |
| **PR #377 (skills.yaml)** | `skills[].name` as the source of truth for available skills |

## Notes on Design Decisions

**Why not TOML/YAML?** JSON is universally parseable without additional dependencies. skills-supply uses TOML but it's the outlier. Every other tool in the ecosystem uses JSON. YAML introduces ambiguity (the Norway problem, etc.). JSON Schema validation is mature and widely supported.

**Why not embed this in SKILL.md frontmatter?** Package-level metadata (author, license, version, repository) doesn't belong in individual skill files. A package manager shouldn't have to parse N markdown files to discover what's available.

**Why `path` is required even when it could be inferred from `name`?** Explicit beats implicit. Packages might use `./skills/pdf` or `./pdf` or `./src/skills/pdf`. No convention to assume.

**Why SRI format for integrity?** It's a W3C standard, already used in browsers and by npm. Format is `algorithm-base64hash`, making the hash algorithm self-describing and forward-compatible with SHA-512 etc.

**Why no `agents` field?** Agent targeting is a consumer preference, not a publisher declaration. A skill that works with Claude Code today will probably work with Cursor tomorrow. The `requires.min_agent_versions` field handles genuine compatibility constraints without dictating installation targets.

**Why `requires.skills` uses `package-name/skill-name` format?** Cross-package dependencies need to be unambiguous. This mirrors Go's module path convention and avoids collision when two packages have a skill with the same name.
