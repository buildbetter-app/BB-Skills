# BB-Skills Restructure Design

**Date:** 2026-04-02
**Status:** Approved
**Author:** Spencer + Claude

## Overview

Restructure the BB-Skills repo from a spec-kit fork into a standalone, skills-first repository. Users install curated packs of AI coding skills for any major platform (Claude Code, Codex, Cursor, Copilot, Gemini, Windsurf, Amazon Q). The repo preserves all BuildBetter-enriched spec-driven development work and adds browser testing skills, a multi-platform adapter layer, and a lightweight CLI for skill management.

## Goals

1. Clean, non-fork repo — fresh push to `buildbetter-app/BB-Skills` with MIT attribution to `github/spec-kit`
2. Skills are the primary artifact — everything else supports installing and updating them
3. Multi-platform — one canonical SKILL.md, adapters convert for each platform
4. Installable packs — users pick what they need (`spec-workflow`, `testing`, or both)
5. User-initiated updates via `bb-skills update` checking GitHub releases
6. Open source — any developer can use it, BuildBetter integration is optional

## Repo Structure

```
BB-Skills/
├── skills/
│   ├── core/
│   │   ├── pack.yml
│   │   └── bb-skills-update/
│   │       └── SKILL.md
│   ├── spec-workflow/
│   │   ├── pack.yml
│   │   ├── specify/
│   │   │   └── SKILL.md
│   │   ├── plan/
│   │   │   └── SKILL.md
│   │   ├── review/
│   │   │   └── SKILL.md
│   │   ├── tasks/
│   │   │   └── SKILL.md
│   │   ├── clarify/
│   │   │   └── SKILL.md
│   │   ├── analyze/
│   │   │   └── SKILL.md
│   │   ├── checklist/
│   │   │   └── SKILL.md
│   │   ├── constitution/
│   │   │   └── SKILL.md
│   │   └── implement/
│   │       └── SKILL.md
│   ├── testing/
│   │   ├── pack.yml
│   │   ├── app-navigator/
│   │   │   └── SKILL.md           # playbooks/ and maps are generated at runtime (gitignored)
│   │   ├── trust-but-verify/
│   │   │   ├── SKILL.md
│   │   │   ├── analysis-prompt.md
│   │   │   └── report-prompt.md
│   │   └── generate-tests/
│   │       └── SKILL.md
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── claude.py
│   ├── codex.py
│   ├── cursor.py
│   ├── copilot.py
│   ├── gemini.py
│   ├── windsurf.py
│   └── amazon_q.py
├── src/bb_skills_cli/
│   ├── __init__.py              # CLI entry point (install, update, list, uninstall, platforms)
│   └── manifest.py              # Manifest read/write for ~/.bb-skills/manifest.json
├── scripts/
│   ├── buildbetter-context.py   # BuildBetter evidence collector (used by spec-workflow skills)
│   ├── bash/
│   │   └── buildbetter-context.sh
│   └── powershell/
│       └── buildbetter-context.ps1
├── templates/
│   ├── spec-template.md         # BB-enriched spec template (used by specify skill)
│   ├── plan-template.md         # BB-enriched plan template (used by plan skill)
│   ├── tasks-template.md
│   ├── checklist-template.md
│   ├── constitution-template.md
│   └── buildbetter-config.conf
├── tests/
│   ├── test_cli.py
│   ├── test_adapters.py
│   └── test_buildbetter_context.py
├── README.md
├── LICENSE                      # MIT with spec-kit attribution
├── pyproject.toml
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## Skill Format

Each skill is a directory containing a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: trust-but-verify
description: Verify feature branch implementations match their plan by testing in a real browser. Use when a feature branch is complete and ready for review.
argument-hint: "[branch-name]"
---

[Skill instructions here — platform-agnostic markdown]
```

**Frontmatter rules:**
- No `model` field — inherits from the user's session on all platforms
- No `@file` references or `` !`bash` `` in the body — Claude Code-specific syntax
- No platform-specific instructions in the main body
- If a skill needs platform-specific notes, use a `# Platform Notes` section that adapters can strip

**Supporting files** (like `analysis-prompt.md`, `report-prompt.md`) live alongside SKILL.md in the same directory. Skills reference them by relative path (e.g., `Read analysis-prompt.md`). On install:
- **Claude, Codex:** supporting files are copied alongside SKILL.md into the skills directory
- **Cursor, Copilot, Windsurf, Amazon Q:** supporting file content is inlined into the converted output since these platforms don't support multi-file skills
- **Gemini:** supporting content is appended to the TOML prompt field

## Pack System

Packs group related skills with metadata in `pack.yml`:

```yaml
name: testing
display_name: "Browser Testing"
description: "Map your app, verify features, generate Playwright tests"
version: "1.0.0"
skills:
  - app-navigator
  - trust-but-verify
  - generate-tests
dependencies:
  - core
```

**Three packs:**

| Pack | Skills | Purpose |
|------|--------|---------|
| `core` | `bb-skills-update` | Update checker — auto-included with any pack |
| `spec-workflow` | `specify`, `plan`, `review`, `tasks`, `clarify`, `analyze`, `checklist`, `constitution`, `implement` | BuildBetter-enriched spec-driven development |
| `testing` | `app-navigator`, `trust-but-verify`, `generate-tests` | Browser-based verification and test generation |

**Install granularity:**
- `bb-skills install testing` — install the whole pack
- `bb-skills install trust-but-verify` — install one skill
- `bb-skills install all` — install everything

## CLI Design

The CLI is `bb-skills`, replacing the old `specify` command. It's a slim Python CLI using Typer + Rich.

### Commands

```
bb-skills install <pack|skill> [--platform auto|claude|codex|cursor|...]
bb-skills update [--check]
bb-skills list [--available|--installed]
bb-skills uninstall <pack|skill>
bb-skills platforms
```

### Install Flow

1. Detect installed platforms (scan for `~/.claude/`, `~/.codex/`, `.cursor/`, etc.)
2. If multiple found, ask which to install for (or use `--platform` flag)
3. Download skill files from latest GitHub release (or use local clone for dev)
4. Run the appropriate adapter to convert SKILL.md to platform format
5. Copy to the correct path per platform (with supporting files)
6. Write `~/.bb-skills/manifest.json` tracking installs

### Update Flow

1. Read `~/.bb-skills/manifest.json` for current version
2. Check `https://api.github.com/repos/buildbetter-app/BB-Skills/releases/latest`
3. Compare versions
4. If newer: show changelog summary, ask to confirm, re-run install for all installed skills/platforms

### Manifest

Stored at `~/.bb-skills/manifest.json`:

```json
{
  "version": "1.0.0",
  "installed_at": "2026-04-02T10:00:00Z",
  "updated_at": "2026-04-02T10:00:00Z",
  "packs": {
    "testing": {
      "skills": ["app-navigator", "trust-but-verify", "generate-tests"]
    },
    "core": {
      "skills": ["bb-skills-update"]
    }
  },
  "platforms": ["claude", "codex", "cursor"]
}
```

### What Gets Dropped from Current CLI

- `extensions.py` (14,917 lines) — the entire extension system
- Extension catalogs (`catalog.json`, `catalog.community.json`)
- `specify init` project scaffolding — replaced by `bb-skills install spec-workflow`
- Agent-specific command file generation — replaced by adapters
- 17-agent AGENT_CONFIG dictionary — replaced by adapter detection

### What Gets Kept

- GitHub release download + retry logic from `__init__.py`
- Interactive selection UI (Rich library)
- BuildBetter context collection scripts (used by spec-workflow skills)
- Platform detection concepts (reimplemented cleanly in adapters)

## Platform Adapters

Each adapter converts canonical SKILL.md to the target format and knows the install path.

| Adapter | Output Format | Install Path | Slash Commands |
|---------|--------------|-------------|----------------|
| `claude` | SKILL.md (minimal changes) | `~/.claude/skills/<name>/` | Yes |
| `codex` | SKILL.md (strip Claude-specific syntax) | `~/.codex/skills/<name>/` | Yes |
| `cursor` | `.mdc` (YAML frontmatter with globs/alwaysApply) | `.cursor/rules/` | No (passive rules) |
| `copilot` | `.instructions.md` (strip frontmatter to prose) | `.github/instructions/` | No (passive instructions) |
| `windsurf` | `.md` (plain markdown, no frontmatter) | `.windsurf/rules/` | No (passive rules) |
| `gemini` | `.toml` (frontmatter → TOML keys, body → prompt) | `~/.gemini/commands/bb-skills/` | Yes |
| `amazon_q` | `.md` (plain markdown with heading structure) | `.amazonq/rules/` | No (passive rules) |

**Adapter interface:**

```python
class BaseAdapter:
    name: str
    
    def convert(self, skill_md: str, metadata: dict) -> str:
        """Convert SKILL.md content to platform format."""
    
    def install_path(self, skill_name: str) -> Path:
        """Return the install path for this skill on this platform."""
    
    def is_available(self) -> bool:
        """Check if this platform is installed/detected."""
    
    def supports_slash_commands(self) -> bool:
        """Whether this platform supports explicit /skill invocation."""
```

**Limitations to document clearly:**
- Cursor, Copilot, Windsurf, Amazon Q: skills become passive context/rules, not invocable commands
- Gemini: TOML format limits rich markdown instructions
- Supporting files (playbooks, prompt templates): only copied for platforms that support multi-file skills (Claude, Codex)

## Update Mechanism

User-initiated only. No background checks, no hooks, no startup latency.

**Command:** `bb-skills update`

**Flow:**
1. Read manifest → get current version
2. Check GitHub releases API → get latest version
3. If current == latest: "You're up to date (v1.2.0)"
4. If newer available:
   ```
   BB-Skills update available: v1.0.0 → v1.2.0

   Changed skills:
     - trust-but-verify: fixed screenshot timing issue
     - specify: added new evidence format support
     - [NEW] code-review: new skill in testing pack

   Update now? [Y/n]
   ```
5. Download new release, re-run adapters, update manifest

**`bb-skills update --check`** — just check, don't install. For scripting/CI.

## README Structure

1. **Hero** — BB-Skills logo, tagline: "AI coding skills enriched with BuildBetter customer evidence"
2. **What is this** — 3-4 sentences. Skills for AI coding agents. Install what you need.
3. **Quick start** — install CLI, pick a pack
4. **Available packs** — table: pack name, skills, description
5. **Platform support** — matrix: platform, format, slash commands (yes/no), install path
6. **Skill reference** — brief per-skill description linking to SKILL.md
7. **BuildBetter integration** — how spec-workflow uses BB evidence (optional)
8. **Updating** — `bb-skills update`
9. **Contributing**
10. **Acknowledgments** — "Inspired by and originally derived from github/spec-kit (MIT). BuildBetter extended the original with customer evidence integration, browser testing skills, multi-platform support, and a skill management CLI."
11. **License** — MIT

## Licensing

- MIT license retained
- Copyright line: "Copyright (c) BuildBetter, Inc. and github/spec-kit contributors"
- Attribution in README acknowledgments section
- No GitHub fork relationship — clean repo, clean history

## Migration Plan (High Level)

1. Create fresh branch (not forked)
2. Set up new directory structure
3. Convert existing spec-kit command templates → SKILL.md format in `skills/spec-workflow/`
4. Copy browser testing skills from `<source-skills-dir>` → `skills/testing/`
5. Build adapter layer (7 adapters)
6. Rewrite CLI as `bb-skills` (install, update, list, uninstall, platforms)
7. Create pack.yml files
8. Migrate BuildBetter context scripts to `scripts/`
9. Migrate templates to `templates/`
10. Write new README
11. Write tests
12. Clean check — ensure no secrets, no spec-kit-only cruft, no broken references
13. First push to fresh `buildbetter-app/BB-Skills` remote

## Open Questions

None — all decisions made during brainstorming.
