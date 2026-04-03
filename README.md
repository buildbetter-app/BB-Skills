# BB-Skills

**AI coding skills enriched with BuildBetter customer evidence.**

---

## What is this?

BB-Skills is a collection of AI coding skills you can install into your favorite AI coding agent. Pick the skills you need -- install only the packs that matter for your workflow. BB-Skills works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf, and Amazon Q.

## Quick start

### Option A: npx (fastest, no install)

```bash
npx skills add buildbetter-app/BB-Skills
```

Or install a specific skill:

```bash
npx skills add buildbetter-app/BB-Skills --skill trust-but-verify
```

### Option B: bb-skills CLI (pack-based install)

```bash
pip install bb-skills
bb-skills install spec-workflow    # spec-driven development skills
bb-skills install testing          # browser testing skills
bb-skills install all              # everything
```

### 3. Use them

Skills are installed into your AI coding agent. On platforms with slash commands (Claude Code, Codex, Gemini):

```
/bb-specify Build a user dashboard with activity feed
/bb-plan
/trust-but-verify
```

On passive platforms (Cursor, Copilot, Windsurf, Amazon Q), skills are injected as context automatically.

## How it works

You run `bb-skills install` once per machine. The CLI auto-detects which AI coding platforms you have installed (`~/.claude/`, `~/.codex/`, `~/.gemini/`, `.cursor/`, etc.) and copies skills to all of them in the correct format.

To see what platforms are detected:

```bash
bb-skills platforms
```

To install for a specific platform only:

```bash
bb-skills install testing --platform claude
```

To install a single skill instead of a whole pack:

```bash
bb-skills install trust-but-verify
```

## Available packs

| Pack | Skills | Description |
|------|--------|-------------|
| `core` | bb-skills-update | Update checker (auto-included) |
| `spec-workflow` | bb-specify, bb-plan, bb-review, bb-tasks, bb-clarify, bb-analyze, bb-checklist, bb-constitution, bb-implement | BuildBetter-enriched spec-driven development |
| `testing` | app-navigator, trust-but-verify, generate-tests | Browser-based verification and Playwright test generation |

## Platform support

| Platform | Format | Slash Commands | Install Path |
|----------|--------|---------------|-------------|
| Claude Code | SKILL.md | Yes | ~/.claude/skills/ |
| Codex CLI | SKILL.md | Yes | ~/.codex/skills/ |
| Cursor | .mdc rules | No (passive) | .cursor/rules/ |
| GitHub Copilot | .instructions.md | No (passive) | .github/instructions/ |
| Gemini CLI | .toml | Yes | ~/.gemini/commands/bb-skills/ |
| Windsurf | .md rules | No (passive) | .windsurf/rules/ |
| Amazon Q | .md rules | No (passive) | .amazonq/rules/ |

## Skill reference

### core

| Skill | Description |
|-------|-------------|
| [bb-skills-update](skills/core/bb-skills-update/) | Checks for available BB-Skills updates via GitHub releases |

### spec-workflow

| Skill | Description |
|-------|-------------|
| [bb-specify](skills/spec-workflow/bb-specify/) | Define what you want to build -- requirements and user stories |
| [bb-plan](skills/spec-workflow/bb-plan/) | Create a technical implementation plan with your chosen tech stack |
| [bb-review](skills/spec-workflow/bb-review/) | BuildBetter-first usability and code review |
| [bb-tasks](skills/spec-workflow/bb-tasks/) | Generate an actionable task list from your implementation plan |
| [bb-clarify](skills/spec-workflow/bb-clarify/) | Clarify underspecified areas before planning |
| [bb-analyze](skills/spec-workflow/bb-analyze/) | Cross-artifact consistency and coverage analysis |
| [bb-checklist](skills/spec-workflow/bb-checklist/) | Generate quality checklists that validate requirements completeness |
| [bb-constitution](skills/spec-workflow/bb-constitution/) | Create or update project governing principles |
| [bb-implement](skills/spec-workflow/bb-implement/) | Execute all tasks to build the feature according to the plan |

### testing

| Skill | Description |
|-------|-------------|
| [app-navigator](skills/testing/app-navigator/) | Map application routes, pages, and components for UI/UX audit |
| [trust-but-verify](skills/testing/trust-but-verify/) | Verify UI/UX and functionality match the original plan |
| [generate-tests](skills/testing/generate-tests/) | Generate reusable Playwright test files from the app map |

## BuildBetter integration

The spec-workflow skills can optionally use BuildBetter's customer evidence API to enrich specifications, plans, and reviews with real customer data. This is not required -- all skills work without it. When a `BUILDBETTER_API_KEY` environment variable is set, the workflow will automatically pull relevant customer insights, feature requests, and pain points into your specs and plans.

To enable it, set the API key in your shell:

```bash
export BUILDBETTER_API_KEY=your_key_here
```

Evidence collection is best-effort and never blocks the workflow. If the key is missing or the API is unreachable, skills continue normally.

## Updating

To update all installed skills to the latest version:

```
bb-skills update
```

## CLI reference

| Command | Description |
|---------|-------------|
| `bb-skills install <pack>` | Install a skill pack |
| `bb-skills uninstall <pack>` | Remove an installed skill pack |
| `bb-skills update` | Update all installed packs to latest |
| `bb-skills list` | List installed packs and skills |
| `bb-skills platforms` | Show supported platforms and install paths |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding skills, writing adapters, and submitting pull requests.

## Acknowledgments

BB-Skills was inspired by and originally derived from [github/spec-kit](https://github.com/github/spec-kit) (MIT License). BuildBetter has significantly extended the original with customer evidence integration, browser testing skills, multi-platform support, and a skill management CLI.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
