# BB-Skills Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure BB-Skills from a spec-kit fork into a standalone, skills-first repo with multi-platform adapters, pack-based installation, and a lightweight CLI.

**Architecture:** Skills are the primary artifact in `skills/<pack>/<skill>/SKILL.md`. A Python CLI (`bb-skills`) handles install/update/list across 7 platforms via adapter modules. Packs group skills for bulk install. A manifest at `~/.bb-skills/manifest.json` tracks state.

**Tech Stack:** Python 3.11+, Typer (CLI), Rich (terminal UI), httpx (HTTP), PyYAML (frontmatter), packaging (versions)

**Spec:** `docs/superpowers/specs/2026-04-02-bb-skills-restructure-design.md`

---

## File Structure

### New files to create:
```
skills/core/pack.yml
skills/core/bb-skills-update/SKILL.md
skills/spec-workflow/pack.yml
skills/spec-workflow/specify/SKILL.md
skills/spec-workflow/plan/SKILL.md
skills/spec-workflow/review/SKILL.md
skills/spec-workflow/tasks/SKILL.md
skills/spec-workflow/clarify/SKILL.md
skills/spec-workflow/analyze/SKILL.md
skills/spec-workflow/checklist/SKILL.md
skills/spec-workflow/constitution/SKILL.md
skills/spec-workflow/implement/SKILL.md
skills/testing/pack.yml
skills/testing/app-navigator/SKILL.md
skills/testing/trust-but-verify/SKILL.md
skills/testing/trust-but-verify/analysis-prompt.md
skills/testing/trust-but-verify/report-prompt.md
skills/testing/generate-tests/SKILL.md
adapters/__init__.py
adapters/base.py
adapters/claude.py
adapters/codex.py
adapters/cursor.py
adapters/copilot.py
adapters/gemini.py
adapters/windsurf.py
adapters/amazon_q.py
src/bb_skills_cli/__init__.py
src/bb_skills_cli/manifest.py
tests/test_cli.py
tests/test_adapters.py
pyproject.toml (rewrite)
README.md (rewrite)
LICENSE (update attribution)
CONTRIBUTING.md (rewrite)
CHANGELOG.md (reset)
.gitignore (new)
```

### Files to keep as-is:
```
scripts/buildbetter-context.py
scripts/bash/buildbetter-context.sh
scripts/powershell/buildbetter-context.ps1
templates/spec-template.md
templates/plan-template.md
templates/tasks-template.md
templates/checklist-template.md
templates/constitution-template.md
templates/buildbetter-config.conf
tests/test_buildbetter_context.py
```

### Files to delete:
```
src/specify_cli/__init__.py          # Replaced by src/bb_skills_cli/__init__.py
src/specify_cli/extensions.py        # Extension system removed
extensions/                          # Entire directory
templates/commands/                  # Converted to skills/spec-workflow/
templates/agent-file-template.md     # No longer needed
templates/vscode-settings.json       # No longer needed
scripts/bash/create-new-feature.sh   # spec-kit scaffolding
scripts/bash/setup-plan.sh           # spec-kit scaffolding
scripts/bash/check-prerequisites.sh  # spec-kit scaffolding
scripts/bash/common.sh               # spec-kit scaffolding
scripts/bash/update-agent-context.sh # spec-kit scaffolding
scripts/powershell/create-new-feature.ps1
scripts/powershell/setup-plan.ps1
scripts/powershell/check-prerequisites.ps1
scripts/powershell/common.ps1
scripts/powershell/update-agent-context.ps1
tests/test_ai_skills.py             # Tests for old CLI
tests/test_cursor_frontmatter.py    # Tests for old CLI
tests/test_extensions.py            # Tests for extension system
spec-driven.md                      # Philosophy doc
AGENTS.md                           # Old agent integration guide
SUPPORT.md                          # spec-kit support
CODE_OF_CONDUCT.md                  # Can add back later
SECURITY.md                         # Can add back later
.github/                            # Old workflows, rebuild later
docs/ (old docs, not superpowers/)  # Old documentation site
logs/                               # Empty/log dir
media/                              # Old logo assets
assets/                             # Old assets
spec-kit.code-workspace             # spec-kit workspace
```

---

## Task 1: Create fresh branch and directory structure

**Files:**
- Create: `skills/core/`, `skills/spec-workflow/`, `skills/testing/`, `adapters/`, `src/bb_skills_cli/`
- Create: `.gitignore`

- [ ] **Step 1: Create the restructure branch**

```bash
cd <repo-root>
git checkout -b restructure/skills-first
```

- [ ] **Step 2: Create all new directories**

```bash
mkdir -p skills/core/bb-skills-update
mkdir -p skills/spec-workflow/{specify,plan,review,tasks,clarify,analyze,checklist,constitution,implement}
mkdir -p skills/testing/{app-navigator,trust-but-verify,generate-tests}
mkdir -p adapters
mkdir -p src/bb_skills_cli
```

- [ ] **Step 3: Create .gitignore**

Write `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
.eggs/

# Virtual environments
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# BB-Skills runtime
skills/testing/app-navigator/playbooks/
skills/testing/app-navigator/app-map.md
skills/testing/app-navigator/component-map.md

# BuildBetter artifacts
.specify/
buildbetter-context.json
buildbetter-context.md
user-stories.md

# Test artifacts
.pytest_cache/
htmlcov/
.coverage
```

- [ ] **Step 4: Commit scaffold**

```bash
git add .gitignore skills/ adapters/ src/bb_skills_cli/
git commit -m "chore: scaffold new skills-first directory structure"
```

---

## Task 2: Create pack.yml files

**Files:**
- Create: `skills/core/pack.yml`
- Create: `skills/spec-workflow/pack.yml`
- Create: `skills/testing/pack.yml`

- [ ] **Step 1: Write core pack.yml**

Write `skills/core/pack.yml`:

```yaml
name: core
display_name: "Core"
description: "Essential BB-Skills utilities including update checking"
version: "1.0.0"
skills:
  - bb-skills-update
dependencies: []
```

- [ ] **Step 2: Write spec-workflow pack.yml**

Write `skills/spec-workflow/pack.yml`:

```yaml
name: spec-workflow
display_name: "Spec-Driven Workflow"
description: "BuildBetter-enriched specification-driven development skills — specify features, plan implementations, generate tasks, and review with customer evidence"
version: "1.0.0"
skills:
  - specify
  - plan
  - review
  - tasks
  - clarify
  - analyze
  - checklist
  - constitution
  - implement
dependencies:
  - core
```

- [ ] **Step 3: Write testing pack.yml**

Write `skills/testing/pack.yml`:

```yaml
name: testing
display_name: "Browser Testing"
description: "Map your app UI, verify feature branches in a real browser, and generate Playwright test suites"
version: "1.0.0"
skills:
  - app-navigator
  - trust-but-verify
  - generate-tests
dependencies:
  - core
```

- [ ] **Step 4: Commit pack definitions**

```bash
git add skills/*/pack.yml
git commit -m "feat: add pack.yml definitions for core, spec-workflow, and testing packs"
```

---

## Task 3: Convert spec-workflow command templates to SKILL.md format

**Files:**
- Read: `templates/commands/specify.md` (284 lines)
- Read: `templates/commands/plan.md` (104 lines)
- Read: `templates/commands/review.md` (128 lines)
- Read: `templates/commands/tasks.md` (142 lines)
- Read: `templates/commands/clarify.md` (184 lines)
- Read: `templates/commands/analyze.md` (187 lines)
- Read: `templates/commands/checklist.md` (297 lines)
- Read: `templates/commands/constitution.md` (84 lines)
- Read: `templates/commands/implement.md` (138 lines)
- Create: `skills/spec-workflow/*/SKILL.md` (9 files)

Each existing command template has YAML frontmatter with `description`, `handoffs`, and optional `scripts` fields. The conversion:
1. Keep `description` from existing frontmatter
2. Add `name` field
3. Drop `handoffs` and `scripts` (these were for the old CLI)
4. Keep the full markdown body (all BB-enriched content)
5. Remove any `@speckit.` or `@bbspec.` slash-command-specific references in the body, make instructions self-contained

- [ ] **Step 1: Read all 9 command templates**

Read each file in `templates/commands/` to understand the current frontmatter and body structure.

- [ ] **Step 2: Convert specify command**

Read `templates/commands/specify.md`. Create `skills/spec-workflow/specify/SKILL.md` with:
- Frontmatter: `name: specify`, `description:` (from existing), drop `handoffs`/`scripts`
- Body: keep all content, replace `/speckit.specify` references with just "this skill", remove shell script invocation steps (the `buildbetter-context.sh` calls become instructions to "run the BuildBetter context collector if available")

- [ ] **Step 3: Convert plan command**

Read `templates/commands/plan.md`. Create `skills/spec-workflow/plan/SKILL.md` with same conversion pattern.

- [ ] **Step 4: Convert review command**

Read `templates/commands/review.md`. Create `skills/spec-workflow/review/SKILL.md`.

- [ ] **Step 5: Convert tasks command**

Read `templates/commands/tasks.md`. Create `skills/spec-workflow/tasks/SKILL.md`.

- [ ] **Step 6: Convert clarify command**

Read `templates/commands/clarify.md`. Create `skills/spec-workflow/clarify/SKILL.md`.

- [ ] **Step 7: Convert analyze command**

Read `templates/commands/analyze.md`. Create `skills/spec-workflow/analyze/SKILL.md`.

- [ ] **Step 8: Convert checklist command**

Read `templates/commands/checklist.md`. Create `skills/spec-workflow/checklist/SKILL.md`.

- [ ] **Step 9: Convert constitution command**

Read `templates/commands/constitution.md`. Create `skills/spec-workflow/constitution/SKILL.md`.

- [ ] **Step 10: Convert implement command**

Read `templates/commands/implement.md`. Create `skills/spec-workflow/implement/SKILL.md`.

- [ ] **Step 11: Commit spec-workflow skills**

```bash
git add skills/spec-workflow/
git commit -m "feat: convert spec-workflow commands to SKILL.md format

Converts all 9 BuildBetter-enriched spec-driven development commands
from templates/commands/*.md to skills/spec-workflow/*/SKILL.md format.
Preserves all BB evidence integration, removes old CLI-specific metadata."
```

---

## Task 4: Copy browser testing skills

**Files:**
- Read: `<source-skills-dir>/app-navigator/SKILL.md` (230 lines)
- Read: `<source-skills-dir>/trust-but-verify/SKILL.md` (226 lines)
- Read: `<source-skills-dir>/trust-but-verify/analysis-prompt.md` (54 lines)
- Read: `<source-skills-dir>/trust-but-verify/report-prompt.md` (99 lines)
- Read: `<source-skills-dir>/generate-tests/SKILL.md` (213 lines)
- Create: `skills/testing/app-navigator/SKILL.md`
- Create: `skills/testing/trust-but-verify/SKILL.md`
- Create: `skills/testing/trust-but-verify/analysis-prompt.md`
- Create: `skills/testing/trust-but-verify/report-prompt.md`
- Create: `skills/testing/generate-tests/SKILL.md`

The app-navigator source also has `app-map.md`, `component-map.md`, and `playbooks/` — these are **generated at runtime** and should NOT be committed (already in .gitignore).

- [ ] **Step 1: Copy app-navigator SKILL.md**

Read `<source-skills-dir>/app-navigator/SKILL.md`. Write to `skills/testing/app-navigator/SKILL.md`. Ensure frontmatter has `name: app-navigator` and a `description` that includes trigger phrases for auto-invocation.

- [ ] **Step 2: Copy trust-but-verify files**

Copy all 3 files from `<source-skills-dir>/trust-but-verify/`:
- `SKILL.md` → `skills/testing/trust-but-verify/SKILL.md`
- `analysis-prompt.md` → `skills/testing/trust-but-verify/analysis-prompt.md`
- `report-prompt.md` → `skills/testing/trust-but-verify/report-prompt.md`

- [ ] **Step 3: Copy generate-tests SKILL.md**

Read `<source-skills-dir>/generate-tests/SKILL.md`. Write to `skills/testing/generate-tests/SKILL.md`.

- [ ] **Step 4: Commit testing skills**

```bash
git add skills/testing/
git commit -m "feat: add browser testing skills (app-navigator, trust-but-verify, generate-tests)"
```

---

## Task 5: Create the bb-skills-update skill

**Files:**
- Create: `skills/core/bb-skills-update/SKILL.md`

- [ ] **Step 1: Write the update skill**

Write `skills/core/bb-skills-update/SKILL.md`:

```markdown
---
name: bb-skills-update
description: Check for and install BB-Skills updates. Use when the user asks to "update skills", "check for updates", or "upgrade bb-skills".
argument-hint: "[--check]"
---

# BB-Skills Update

Check for available updates to installed BB-Skills.

## Instructions

1. Read the manifest at `~/.bb-skills/manifest.json` to find the current installed version
2. If the manifest doesn't exist, tell the user to install BB-Skills first: `pip install bb-skills-cli` then `bb-skills install <pack>`
3. Run: `bb-skills update` (or `bb-skills update --check` if user only wants to check without installing)
4. Report the result to the user

## If bb-skills CLI is not installed

Tell the user:
> BB-Skills CLI is not installed. Install it with:
> ```
> pip install bb-skills-cli
> ```
> Then run `bb-skills install <pack>` to install skill packs.
```

- [ ] **Step 2: Commit core skill**

```bash
git add skills/core/
git commit -m "feat: add bb-skills-update core skill"
```

---

## Task 6: Build the adapter base and Claude adapter

**Files:**
- Create: `adapters/__init__.py`
- Create: `adapters/base.py`
- Create: `adapters/claude.py`
- Test: `tests/test_adapters.py`

- [ ] **Step 1: Write failing test for base adapter interface**

Write `tests/test_adapters.py`:

```python
"""Tests for platform adapters."""

import pytest
from pathlib import Path
from adapters.base import BaseAdapter, parse_skill_frontmatter


class TestParseFrontmatter:
    def test_parses_yaml_frontmatter(self):
        content = """---
name: test-skill
description: A test skill
argument-hint: "[args]"
---

# Test Skill

Do the thing."""
        metadata, body = parse_skill_frontmatter(content)
        assert metadata["name"] == "test-skill"
        assert metadata["description"] == "A test skill"
        assert metadata["argument-hint"] == "[args]"
        assert body.strip().startswith("# Test Skill")

    def test_no_frontmatter(self):
        content = "# Just markdown\n\nNo frontmatter here."
        metadata, body = parse_skill_frontmatter(content)
        assert metadata == {}
        assert body == content

    def test_empty_frontmatter(self):
        content = "---\n---\n\nBody here."
        metadata, body = parse_skill_frontmatter(content)
        assert metadata == {}
        assert body.strip() == "Body here."


class TestBaseAdapter:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseAdapter()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd <repo-root>
python -m pytest tests/test_adapters.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'adapters'`

- [ ] **Step 3: Write adapters/__init__.py**

Write `adapters/__init__.py`:

```python
"""Platform adapters for converting SKILL.md to target formats."""

from adapters.base import BaseAdapter, parse_skill_frontmatter

__all__ = ["BaseAdapter", "parse_skill_frontmatter"]
```

- [ ] **Step 4: Write adapters/base.py**

Write `adapters/base.py`:

```python
"""Base adapter interface and shared utilities."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import yaml


def parse_skill_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns (metadata_dict, body_string).
    """
    if not content.startswith("---"):
        return {}, content

    # Find closing ---
    end = content.find("---", 3)
    if end == -1:
        return {}, content

    frontmatter_str = content[3:end].strip()
    body = content[end + 3:].strip()

    if not frontmatter_str:
        return {}, body

    metadata = yaml.safe_load(frontmatter_str) or {}
    return metadata, body


def read_skill_directory(skill_dir: Path) -> tuple[str, dict[str, str]]:
    """Read a skill directory, returning (skill_md_content, {filename: content}).

    The SKILL.md content is returned separately. All other .md files are
    returned in the supporting_files dict.
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_dir}")

    skill_content = skill_md.read_text(encoding="utf-8")

    supporting = {}
    for f in skill_dir.iterdir():
        if f.name == "SKILL.md":
            continue
        if f.is_file() and f.suffix == ".md":
            supporting[f.name] = f.read_text(encoding="utf-8")
        elif f.is_dir():
            # Skip directories (like playbooks/) — they're runtime-generated
            pass

    return skill_content, supporting


class BaseAdapter(ABC):
    """Base class for platform adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform name (e.g., 'claude', 'codex')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable platform name."""
        ...

    @abstractmethod
    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Convert SKILL.md + supporting files to platform format.

        Returns a dict of {relative_filename: content} to write.
        """
        ...

    @abstractmethod
    def install_path(self, skill_name: str) -> Path:
        """Return the install directory for this skill on this platform."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this platform is detected on the system."""
        ...

    @property
    def supports_slash_commands(self) -> bool:
        """Whether this platform supports explicit /skill invocation."""
        return False

    @property
    def supports_multi_file(self) -> bool:
        """Whether this platform supports multi-file skill directories."""
        return False
```

- [ ] **Step 5: Run test to verify base passes**

```bash
python -m pytest tests/test_adapters.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 6: Write failing test for Claude adapter**

Append to `tests/test_adapters.py`:

```python
from adapters.claude import ClaudeAdapter


class TestClaudeAdapter:
    def setup_method(self):
        self.adapter = ClaudeAdapter()

    def test_name(self):
        assert self.adapter.name == "claude"
        assert self.adapter.display_name == "Claude Code"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is True

    def test_supports_multi_file(self):
        assert self.adapter.supports_multi_file is True

    def test_convert_passes_through(self):
        skill = """---
name: test
description: A test
---

# Test"""
        supporting = {"helper.md": "# Helper content"}
        result = self.adapter.convert(skill, supporting)
        assert "SKILL.md" in result
        assert "helper.md" in result
        assert result["SKILL.md"] == skill
        assert result["helper.md"] == "# Helper content"

    def test_install_path(self):
        path = self.adapter.install_path("trust-but-verify")
        assert path == Path.home() / ".claude" / "skills" / "trust-but-verify"

    def test_is_available(self):
        # Should return True if ~/.claude exists
        result = self.adapter.is_available()
        assert isinstance(result, bool)
```

- [ ] **Step 7: Run test to verify it fails**

```bash
python -m pytest tests/test_adapters.py::TestClaudeAdapter -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.claude'`

- [ ] **Step 8: Write adapters/claude.py**

Write `adapters/claude.py`:

```python
"""Claude Code adapter — SKILL.md passthrough with multi-file support."""

from pathlib import Path

from adapters.base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "claude"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Claude Code uses SKILL.md natively — passthrough."""
        result = {"SKILL.md": skill_content}
        result.update(supporting_files)
        return result

    def install_path(self, skill_name: str) -> Path:
        return Path.home() / ".claude" / "skills" / skill_name

    def is_available(self) -> bool:
        return (Path.home() / ".claude").is_dir()

    @property
    def supports_slash_commands(self) -> bool:
        return True

    @property
    def supports_multi_file(self) -> bool:
        return True
```

- [ ] **Step 9: Run tests**

```bash
python -m pytest tests/test_adapters.py -v
```

Expected: ALL PASS

- [ ] **Step 10: Commit**

```bash
git add adapters/__init__.py adapters/base.py adapters/claude.py tests/test_adapters.py
git commit -m "feat: add base adapter interface and Claude Code adapter"
```

---

## Task 7: Build remaining adapters (Codex, Cursor, Copilot, Gemini, Windsurf, Amazon Q)

**Files:**
- Create: `adapters/codex.py`
- Create: `adapters/cursor.py`
- Create: `adapters/copilot.py`
- Create: `adapters/gemini.py`
- Create: `adapters/windsurf.py`
- Create: `adapters/amazon_q.py`
- Modify: `tests/test_adapters.py`

- [ ] **Step 1: Write failing tests for all 6 adapters**

Append to `tests/test_adapters.py`:

```python
from adapters.codex import CodexAdapter
from adapters.cursor import CursorAdapter
from adapters.copilot import CopilotAdapter
from adapters.gemini import GeminiAdapter
from adapters.windsurf import WindsurfAdapter
from adapters.amazon_q import AmazonQAdapter


class TestCodexAdapter:
    def setup_method(self):
        self.adapter = CodexAdapter()

    def test_name(self):
        assert self.adapter.name == "codex"
        assert self.adapter.display_name == "Codex CLI"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is True

    def test_supports_multi_file(self):
        assert self.adapter.supports_multi_file is True

    def test_convert_passthrough(self):
        skill = """---
name: test
description: A test
---

# Test"""
        result = self.adapter.convert(skill, {"helper.md": "content"})
        assert "SKILL.md" in result
        assert "helper.md" in result

    def test_install_path(self):
        path = self.adapter.install_path("my-skill")
        assert path == Path.home() / ".codex" / "skills" / "my-skill"


class TestCursorAdapter:
    def setup_method(self):
        self.adapter = CursorAdapter()

    def test_name(self):
        assert self.adapter.name == "cursor"

    def test_no_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_no_multi_file(self):
        assert self.adapter.supports_multi_file is False

    def test_convert_to_mdc(self):
        skill = """---
name: test-skill
description: A test skill for testing
---

# Test Skill

Follow these instructions."""
        result = self.adapter.convert(skill, {})
        assert len(result) == 1
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test-skill.mdc"
        content = result[filename]
        assert "description: A test skill for testing" in content
        assert "alwaysApply: true" in content
        assert "# Test Skill" in content

    def test_convert_inlines_supporting_files(self):
        skill = """---
name: test
description: Test
---

# Main"""
        supporting = {"helper.md": "# Helper\n\nHelper content here."}
        result = self.adapter.convert(skill, supporting)
        content = list(result.values())[0]
        assert "# Helper" in content
        assert "Helper content here." in content

    def test_install_path(self):
        path = self.adapter.install_path("my-skill")
        assert path == Path.cwd() / ".cursor" / "rules"


class TestCopilotAdapter:
    def setup_method(self):
        self.adapter = CopilotAdapter()

    def test_name(self):
        assert self.adapter.name == "copilot"

    def test_no_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_convert_strips_frontmatter(self):
        skill = """---
name: test
description: A test
---

# Test Skill

Instructions here."""
        result = self.adapter.convert(skill, {})
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test.instructions.md"
        content = result[filename]
        assert "---" not in content
        assert "# Test Skill" in content

    def test_install_path(self):
        path = self.adapter.install_path("my-skill")
        assert path == Path.cwd() / ".github" / "instructions"


class TestGeminiAdapter:
    def setup_method(self):
        self.adapter = GeminiAdapter()

    def test_name(self):
        assert self.adapter.name == "gemini"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is True

    def test_convert_to_toml(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill

Do the thing."""
        result = self.adapter.convert(skill, {})
        filename = list(result.keys())[0]
        assert filename == "test-skill.toml"
        content = result[filename]
        assert 'description = "A test skill"' in content
        assert "# Test Skill" in content

    def test_install_path(self):
        path = self.adapter.install_path("my-skill")
        assert path == Path.home() / ".gemini" / "commands" / "bb-skills"


class TestWindsurfAdapter:
    def setup_method(self):
        self.adapter = WindsurfAdapter()

    def test_name(self):
        assert self.adapter.name == "windsurf"

    def test_no_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_convert_plain_markdown(self):
        skill = """---
name: test
description: A test
---

# Test Skill

Instructions."""
        result = self.adapter.convert(skill, {})
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test.md"
        content = result[filename]
        assert "---" not in content
        assert "# Test Skill" in content

    def test_install_path(self):
        path = self.adapter.install_path("my-skill")
        assert path == Path.cwd() / ".windsurf" / "rules"


class TestAmazonQAdapter:
    def setup_method(self):
        self.adapter = AmazonQAdapter()

    def test_name(self):
        assert self.adapter.name == "amazon-q"

    def test_no_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_convert_plain_markdown(self):
        skill = """---
name: test
description: A test skill
---

# Test Skill

Instructions."""
        result = self.adapter.convert(skill, {})
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test.md"
        content = result[filename]
        assert "---" not in content
        assert "# Test Skill" in content

    def test_install_path(self):
        path = self.adapter.install_path("my-skill")
        assert path == Path.cwd() / ".amazonq" / "rules"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_adapters.py -v --tb=short 2>&1 | head -30
```

Expected: FAIL — missing adapter modules

- [ ] **Step 3: Write adapters/codex.py**

```python
"""Codex CLI adapter — SKILL.md passthrough with multi-file support."""

from pathlib import Path

from adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "codex"

    @property
    def display_name(self) -> str:
        return "Codex CLI"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Codex uses SKILL.md natively — passthrough."""
        result = {"SKILL.md": skill_content}
        result.update(supporting_files)
        return result

    def install_path(self, skill_name: str) -> Path:
        return Path.home() / ".codex" / "skills" / skill_name

    def is_available(self) -> bool:
        return (Path.home() / ".codex").is_dir()

    @property
    def supports_slash_commands(self) -> bool:
        return True

    @property
    def supports_multi_file(self) -> bool:
        return True
```

- [ ] **Step 4: Write adapters/cursor.py**

```python
"""Cursor adapter — converts SKILL.md to .mdc rule format."""

from pathlib import Path

from adapters.base import BaseAdapter, parse_skill_frontmatter


class CursorAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "cursor"

    @property
    def display_name(self) -> str:
        return "Cursor"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Convert SKILL.md to Cursor .mdc format with inlined supporting files."""
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unknown")
        description = metadata.get("description", "")

        # Build .mdc frontmatter
        mdc_parts = [
            "---",
            f"description: {description}",
            "alwaysApply: true",
            "---",
            "",
            body,
        ]

        # Inline supporting files at the end
        for filename, content in supporting_files.items():
            mdc_parts.append("")
            mdc_parts.append(f"---")
            mdc_parts.append(f"")
            mdc_parts.append(f"## Reference: {filename}")
            mdc_parts.append("")
            mdc_parts.append(content)

        output = "\n".join(mdc_parts)
        return {f"bb-skills-{skill_name}.mdc": output}

    def install_path(self, skill_name: str) -> Path:
        return Path.cwd() / ".cursor" / "rules"

    def is_available(self) -> bool:
        return (Path.cwd() / ".cursor").is_dir()
```

- [ ] **Step 5: Write adapters/copilot.py**

```python
"""GitHub Copilot adapter — converts SKILL.md to .instructions.md format."""

from pathlib import Path

from adapters.base import BaseAdapter, parse_skill_frontmatter


class CopilotAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "copilot"

    @property
    def display_name(self) -> str:
        return "GitHub Copilot"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Strip frontmatter, output plain markdown instructions."""
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unknown")

        parts = [body]
        for filename, content in supporting_files.items():
            parts.append(f"\n\n## Reference: {filename}\n\n{content}")

        output = "\n".join(parts)
        return {f"bb-skills-{skill_name}.instructions.md": output}

    def install_path(self, skill_name: str) -> Path:
        return Path.cwd() / ".github" / "instructions"

    def is_available(self) -> bool:
        return (Path.cwd() / ".github").is_dir()
```

- [ ] **Step 6: Write adapters/gemini.py**

```python
"""Gemini CLI adapter — converts SKILL.md to TOML command format."""

from pathlib import Path

from adapters.base import BaseAdapter, parse_skill_frontmatter


class GeminiAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Gemini CLI"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Convert SKILL.md to Gemini TOML command format."""
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unknown")
        description = metadata.get("description", "")

        # Inline supporting files into the prompt body
        full_body = body
        for filename, content in supporting_files.items():
            full_body += f"\n\n## Reference: {filename}\n\n{content}"

        # Escape for TOML multi-line string
        escaped_body = full_body.replace('\\', '\\\\').replace('"""', '\\"\\"\\"')

        toml_content = f'description = "{description}"\n\nprompt = """\n{escaped_body}\n"""'
        return {f"{skill_name}.toml": toml_content}

    def install_path(self, skill_name: str) -> Path:
        return Path.home() / ".gemini" / "commands" / "bb-skills"

    def is_available(self) -> bool:
        return (Path.home() / ".gemini").is_dir()

    @property
    def supports_slash_commands(self) -> bool:
        return True
```

- [ ] **Step 7: Write adapters/windsurf.py**

```python
"""Windsurf adapter — converts SKILL.md to plain markdown rules."""

from pathlib import Path

from adapters.base import BaseAdapter, parse_skill_frontmatter


class WindsurfAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "windsurf"

    @property
    def display_name(self) -> str:
        return "Windsurf"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Strip frontmatter, output plain markdown."""
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unknown")

        parts = [body]
        for filename, content in supporting_files.items():
            parts.append(f"\n\n## Reference: {filename}\n\n{content}")

        output = "\n".join(parts)
        return {f"bb-skills-{skill_name}.md": output}

    def install_path(self, skill_name: str) -> Path:
        return Path.cwd() / ".windsurf" / "rules"

    def is_available(self) -> bool:
        return (Path.cwd() / ".windsurf").is_dir()
```

- [ ] **Step 8: Write adapters/amazon_q.py**

```python
"""Amazon Q Developer adapter — converts SKILL.md to plain markdown rules."""

from pathlib import Path

from adapters.base import BaseAdapter, parse_skill_frontmatter


class AmazonQAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "amazon-q"

    @property
    def display_name(self) -> str:
        return "Amazon Q Developer"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        """Strip frontmatter, output plain markdown with heading structure."""
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unknown")

        parts = [body]
        for filename, content in supporting_files.items():
            parts.append(f"\n\n## Reference: {filename}\n\n{content}")

        output = "\n".join(parts)
        return {f"bb-skills-{skill_name}.md": output}

    def install_path(self, skill_name: str) -> Path:
        return Path.cwd() / ".amazonq" / "rules"

    def is_available(self) -> bool:
        return (Path.cwd() / ".amazonq").is_dir()
```

- [ ] **Step 9: Update adapters/__init__.py with all adapters**

Replace `adapters/__init__.py`:

```python
"""Platform adapters for converting SKILL.md to target formats."""

from adapters.base import BaseAdapter, parse_skill_frontmatter, read_skill_directory
from adapters.claude import ClaudeAdapter
from adapters.codex import CodexAdapter
from adapters.cursor import CursorAdapter
from adapters.copilot import CopilotAdapter
from adapters.gemini import GeminiAdapter
from adapters.windsurf import WindsurfAdapter
from adapters.amazon_q import AmazonQAdapter

ALL_ADAPTERS = [
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    CopilotAdapter,
    GeminiAdapter,
    WindsurfAdapter,
    AmazonQAdapter,
]

__all__ = [
    "BaseAdapter",
    "parse_skill_frontmatter",
    "read_skill_directory",
    "ALL_ADAPTERS",
    "ClaudeAdapter",
    "CodexAdapter",
    "CursorAdapter",
    "CopilotAdapter",
    "GeminiAdapter",
    "WindsurfAdapter",
    "AmazonQAdapter",
]
```

- [ ] **Step 10: Run all adapter tests**

```bash
python -m pytest tests/test_adapters.py -v
```

Expected: ALL PASS

- [ ] **Step 11: Commit**

```bash
git add adapters/ tests/test_adapters.py
git commit -m "feat: add all 7 platform adapters (Claude, Codex, Cursor, Copilot, Gemini, Windsurf, Amazon Q)"
```

---

## Task 8: Build the manifest module

**Files:**
- Create: `src/bb_skills_cli/manifest.py`
- Create: `tests/test_cli.py` (start with manifest tests)

- [ ] **Step 1: Write failing tests for manifest**

Write `tests/test_cli.py`:

```python
"""Tests for bb-skills CLI."""

import json
import pytest
from pathlib import Path

from bb_skills_cli.manifest import Manifest


class TestManifest:
    def test_load_missing_file(self, tmp_path):
        m = Manifest(tmp_path / "manifest.json")
        assert m.version is None
        assert m.packs == {}
        assert m.platforms == []

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "manifest.json"
        m = Manifest(path)
        m.version = "1.0.0"
        m.packs = {"testing": {"skills": ["app-navigator", "trust-but-verify"]}}
        m.platforms = ["claude", "codex"]
        m.save()

        loaded = Manifest(path)
        assert loaded.version == "1.0.0"
        assert loaded.packs == {"testing": {"skills": ["app-navigator", "trust-but-verify"]}}
        assert loaded.platforms == ["claude", "codex"]

    def test_add_pack(self, tmp_path):
        m = Manifest(tmp_path / "manifest.json")
        m.add_pack("testing", ["app-navigator", "trust-but-verify"])
        assert "testing" in m.packs
        assert m.packs["testing"]["skills"] == ["app-navigator", "trust-but-verify"]

    def test_remove_pack(self, tmp_path):
        m = Manifest(tmp_path / "manifest.json")
        m.add_pack("testing", ["app-navigator"])
        m.remove_pack("testing")
        assert "testing" not in m.packs

    def test_remove_nonexistent_pack(self, tmp_path):
        m = Manifest(tmp_path / "manifest.json")
        m.remove_pack("nope")  # Should not raise

    def test_has_skill(self, tmp_path):
        m = Manifest(tmp_path / "manifest.json")
        m.add_pack("testing", ["app-navigator", "trust-but-verify"])
        assert m.has_skill("app-navigator") is True
        assert m.has_skill("nonexistent") is False

    def test_default_path(self):
        m = Manifest()
        assert m.path == Path.home() / ".bb-skills" / "manifest.json"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd <repo-root>
PYTHONPATH=src:. python -m pytest tests/test_cli.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write src/bb_skills_cli/__init__.py stub**

Write `src/bb_skills_cli/__init__.py`:

```python
"""BB-Skills CLI — install, update, and manage AI coding skills."""

__version__ = "1.0.0"
```

- [ ] **Step 4: Write src/bb_skills_cli/manifest.py**

```python
"""Manifest tracking for installed BB-Skills."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class Manifest:
    """Tracks installed skills, versions, and platforms."""

    DEFAULT_PATH = Path.home() / ".bb-skills" / "manifest.json"

    def __init__(self, path: Optional[Path] = None):
        self.path = path or self.DEFAULT_PATH
        self.version: Optional[str] = None
        self.installed_at: Optional[str] = None
        self.updated_at: Optional[str] = None
        self.packs: dict[str, dict] = {}
        self.platforms: list[str] = []
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.version = data.get("version")
        self.installed_at = data.get("installed_at")
        self.updated_at = data.get("updated_at")
        self.packs = data.get("packs", {})
        self.platforms = data.get("platforms", [])

    def save(self):
        now = datetime.now(timezone.utc).isoformat()
        if self.installed_at is None:
            self.installed_at = now
        self.updated_at = now

        data = {
            "version": self.version,
            "installed_at": self.installed_at,
            "updated_at": self.updated_at,
            "packs": self.packs,
            "platforms": self.platforms,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def add_pack(self, pack_name: str, skills: list[str]):
        self.packs[pack_name] = {"skills": skills}

    def remove_pack(self, pack_name: str):
        self.packs.pop(pack_name, None)

    def has_skill(self, skill_name: str) -> bool:
        for pack_data in self.packs.values():
            if skill_name in pack_data.get("skills", []):
                return True
        return False
```

- [ ] **Step 5: Run tests**

```bash
PYTHONPATH=src:. python -m pytest tests/test_cli.py -v
```

Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add src/bb_skills_cli/ tests/test_cli.py
git commit -m "feat: add manifest module for tracking installed skills"
```

---

## Task 9: Build the CLI (install, update, list, uninstall, platforms)

**Files:**
- Modify: `src/bb_skills_cli/__init__.py`
- Modify: `tests/test_cli.py`

This is the largest task. The CLI uses Typer + Rich and reuses download logic concepts from the old `specify_cli/__init__.py` (lines 711-896).

- [ ] **Step 1: Write failing tests for CLI commands**

Append to `tests/test_cli.py`:

```python
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from bb_skills_cli import create_app


runner = CliRunner()


class TestCLIList:
    def test_list_available(self, tmp_path):
        app = create_app(skills_dir=tmp_path)
        # Create a minimal pack structure
        pack_dir = tmp_path / "testing"
        pack_dir.mkdir()
        (pack_dir / "pack.yml").write_text(
            "name: testing\ndisplay_name: Browser Testing\n"
            "description: Test skills\nversion: 1.0.0\n"
            "skills:\n  - app-navigator\ndependencies: []\n"
        )
        skill_dir = pack_dir / "app-navigator"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: app-navigator\ndescription: Map app\n---\n\n# Nav")

        result = runner.invoke(app, ["list", "--available"])
        assert result.exit_code == 0
        assert "testing" in result.output
        assert "app-navigator" in result.output


class TestCLIPlatforms:
    def test_platforms_command(self):
        app = create_app()
        result = runner.invoke(app, ["platforms"])
        assert result.exit_code == 0
        # Should list detected platforms
        assert "Platform" in result.output or "platform" in result.output
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src:. python -m pytest tests/test_cli.py::TestCLIList -v
```

Expected: FAIL — `cannot import name 'create_app'`

- [ ] **Step 3: Write the full CLI**

Replace `src/bb_skills_cli/__init__.py`:

```python
"""BB-Skills CLI — install, update, and manage AI coding skills."""

__version__ = "1.0.0"

import sys
from pathlib import Path
from typing import Optional

import httpx
import typer
import yaml
from rich.console import Console
from rich.table import Table

from bb_skills_cli.manifest import Manifest

# Add project root to path for adapter imports
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from adapters import ALL_ADAPTERS, read_skill_directory

console = Console()

GITHUB_REPO = "buildbetter-app/BB-Skills"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _find_skills_dir() -> Path:
    """Find the skills/ directory — local clone or downloaded."""
    # Check if running from a local clone
    local = _project_root / "skills"
    if local.is_dir():
        return local
    # Fallback: downloaded to ~/.bb-skills/skills/
    return Path.home() / ".bb-skills" / "skills"


def _load_pack(pack_dir: Path) -> dict:
    """Load pack.yml from a pack directory."""
    pack_file = pack_dir / "pack.yml"
    if not pack_file.exists():
        return {}
    return yaml.safe_load(pack_file.read_text(encoding="utf-8"))


def _discover_packs(skills_dir: Path) -> dict[str, dict]:
    """Discover all packs in the skills directory."""
    packs = {}
    if not skills_dir.is_dir():
        return packs
    for child in sorted(skills_dir.iterdir()):
        if child.is_dir() and (child / "pack.yml").exists():
            packs[child.name] = _load_pack(child)
    return packs


def _find_skill_pack(skill_name: str, packs: dict[str, dict]) -> Optional[str]:
    """Find which pack a skill belongs to."""
    for pack_name, pack_data in packs.items():
        if skill_name in pack_data.get("skills", []):
            return pack_name
    return None


def _get_available_adapters() -> list:
    """Return adapter instances for all detected platforms."""
    available = []
    for adapter_cls in ALL_ADAPTERS:
        adapter = adapter_cls()
        if adapter.is_available():
            available.append(adapter)
    return available


def _install_skill(skill_dir: Path, adapter, skill_name: str):
    """Install a single skill to a platform via its adapter."""
    skill_content, supporting = read_skill_directory(skill_dir)
    converted = adapter.convert(skill_content, supporting)
    install_dir = adapter.install_path(skill_name)
    install_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in converted.items():
        target = install_dir / filename
        target.write_text(content, encoding="utf-8")

    return install_dir


def _resolve_targets(names: list[str], skills_dir: Path, packs: dict) -> list[tuple[str, str, Path]]:
    """Resolve pack/skill names to (pack_name, skill_name, skill_dir) tuples."""
    targets = []

    for name in names:
        if name == "all":
            for pack_name, pack_data in packs.items():
                for skill_name in pack_data.get("skills", []):
                    skill_path = skills_dir / pack_name / skill_name
                    if skill_path.is_dir():
                        targets.append((pack_name, skill_name, skill_path))
            return targets

        # Check if it's a pack name
        if name in packs:
            pack_data = packs[name]
            # Also install dependencies
            for dep in pack_data.get("dependencies", []):
                if dep in packs:
                    for skill_name in packs[dep].get("skills", []):
                        skill_path = skills_dir / dep / skill_name
                        if skill_path.is_dir():
                            targets.append((dep, skill_name, skill_path))
            # Install pack skills
            for skill_name in pack_data.get("skills", []):
                skill_path = skills_dir / name / skill_name
                if skill_path.is_dir():
                    targets.append((name, skill_name, skill_path))
            continue

        # Check if it's an individual skill name
        pack_name = _find_skill_pack(name, packs)
        if pack_name:
            skill_path = skills_dir / pack_name / name
            if skill_path.is_dir():
                # Also install core dependency
                if "core" in packs and pack_name != "core":
                    for core_skill in packs["core"].get("skills", []):
                        core_path = skills_dir / "core" / core_skill
                        if core_path.is_dir():
                            targets.append(("core", core_skill, core_path))
                targets.append((pack_name, name, skill_path))
            continue

        console.print(f"[red]Unknown pack or skill: {name}[/red]")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in targets:
        key = (item[0], item[1])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def create_app(skills_dir: Optional[Path] = None) -> typer.Typer:
    """Create the Typer app. Accepts skills_dir override for testing."""

    app = typer.Typer(
        name="bb-skills",
        help="Install and manage BB-Skills for your AI coding agent.",
        no_args_is_help=True,
    )

    resolved_skills_dir = skills_dir or _find_skills_dir()

    @app.command()
    def install(
        names: list[str] = typer.Argument(help="Pack or skill names to install"),
        platform: Optional[str] = typer.Option(None, help="Target platform (auto-detect if omitted)"),
    ):
        """Install skill packs or individual skills."""
        packs = _discover_packs(resolved_skills_dir)
        if not packs:
            console.print("[red]No skills found. Are you in the BB-Skills repo or has it been downloaded?[/red]")
            raise typer.Exit(1)

        targets = _resolve_targets(names, resolved_skills_dir, packs)
        if not targets:
            console.print("[red]No valid skills to install.[/red]")
            raise typer.Exit(1)

        # Determine adapters
        if platform:
            platform_names = [p.strip() for p in platform.split(",")]
            adapters = [cls() for cls in ALL_ADAPTERS if cls().name in platform_names]
        else:
            adapters = _get_available_adapters()

        if not adapters:
            console.print("[red]No supported platforms detected. Use --platform to specify.[/red]")
            raise typer.Exit(1)

        manifest = Manifest()

        for adapter in adapters:
            console.print(f"\n[bold]{adapter.display_name}[/bold]", highlight=False)
            slash = " (slash commands)" if adapter.supports_slash_commands else " (passive rules)"
            console.print(f"  Mode:{slash}", highlight=False)

            for pack_name, skill_name, skill_path in targets:
                install_dir = _install_skill(skill_path, adapter, skill_name)
                console.print(f"  [green]+[/green] {skill_name} -> {install_dir}")

        # Update manifest
        manifest.version = __version__
        manifest.platforms = list({a.name for a in adapters})
        installed_packs: dict[str, list[str]] = {}
        for pack_name, skill_name, _ in targets:
            installed_packs.setdefault(pack_name, []).append(skill_name)
        for pack_name, skill_list in installed_packs.items():
            manifest.add_pack(pack_name, skill_list)
        manifest.save()

        console.print(f"\n[green]Installed {len(targets)} skill(s) to {len(adapters)} platform(s).[/green]")

    @app.command()
    def update(
        check: bool = typer.Option(False, "--check", help="Check only, don't install"),
    ):
        """Check for and install BB-Skills updates."""
        manifest = Manifest()

        if manifest.version is None:
            console.print("[yellow]No BB-Skills installed. Run: bb-skills install <pack>[/yellow]")
            raise typer.Exit(1)

        console.print(f"Current version: {manifest.version}")
        console.print("Checking for updates...")

        try:
            resp = httpx.get(RELEASES_URL, timeout=10, follow_redirects=True)
            resp.raise_for_status()
            release = resp.json()
        except httpx.HTTPError as e:
            console.print(f"[red]Failed to check for updates: {e}[/red]")
            raise typer.Exit(1)

        latest = release.get("tag_name", "").lstrip("v")
        if not latest:
            console.print("[red]Could not determine latest version.[/red]")
            raise typer.Exit(1)

        if latest == manifest.version:
            console.print(f"[green]You're up to date (v{latest}).[/green]")
            return

        console.print(f"\n[bold]Update available: v{manifest.version} -> v{latest}[/bold]")
        body = release.get("body", "No release notes.")
        console.print(f"\n{body}\n")

        if check:
            return

        if not typer.confirm("Update now?"):
            return

        # Re-install all currently installed skills
        packs = _discover_packs(resolved_skills_dir)
        all_targets = []
        for pack_name, pack_data in manifest.packs.items():
            for skill_name in pack_data.get("skills", []):
                skill_path = resolved_skills_dir / pack_name / skill_name
                if skill_path.is_dir():
                    all_targets.append((pack_name, skill_name, skill_path))

        adapters = [cls() for cls in ALL_ADAPTERS if cls().name in manifest.platforms]

        for adapter in adapters:
            for pack_name, skill_name, skill_path in all_targets:
                _install_skill(skill_path, adapter, skill_name)

        manifest.version = latest
        manifest.save()
        console.print(f"\n[green]Updated to v{latest}.[/green]")

    @app.command(name="list")
    def list_skills(
        available: bool = typer.Option(False, "--available", help="Show available skills"),
        installed: bool = typer.Option(False, "--installed", help="Show installed skills"),
    ):
        """List available or installed skills."""
        if installed or not available:
            manifest = Manifest()
            if not manifest.packs:
                console.print("[yellow]No skills installed. Run: bb-skills install <pack>[/yellow]")
                if not available:
                    return

        if available or not installed:
            packs = _discover_packs(resolved_skills_dir)
            table = Table(title="Available Packs & Skills")
            table.add_column("Pack", style="bold")
            table.add_column("Skill")
            table.add_column("Description")

            for pack_name, pack_data in packs.items():
                first = True
                for skill_name in pack_data.get("skills", []):
                    skill_dir = resolved_skills_dir / pack_name / skill_name / "SKILL.md"
                    desc = ""
                    if skill_dir.exists():
                        from adapters.base import parse_skill_frontmatter
                        meta, _ = parse_skill_frontmatter(skill_dir.read_text(encoding="utf-8"))
                        desc = meta.get("description", "")[:80]
                    pack_label = f"{pack_name} ({pack_data.get('display_name', '')})" if first else ""
                    table.add_row(pack_label, skill_name, desc)
                    first = False

            console.print(table)

        if installed:
            manifest = Manifest()
            if manifest.packs:
                table = Table(title="Installed Skills")
                table.add_column("Pack")
                table.add_column("Skills")
                table.add_column("Platforms")
                for pack_name, pack_data in manifest.packs.items():
                    table.add_row(pack_name, ", ".join(pack_data["skills"]), ", ".join(manifest.platforms))
                console.print(table)

    @app.command()
    def uninstall(
        names: list[str] = typer.Argument(help="Pack or skill names to uninstall"),
    ):
        """Uninstall skill packs or individual skills."""
        manifest = Manifest()
        if not manifest.packs:
            console.print("[yellow]No skills installed.[/yellow]")
            raise typer.Exit(1)

        packs = _discover_packs(resolved_skills_dir)
        adapters = [cls() for cls in ALL_ADAPTERS if cls().name in manifest.platforms]

        for name in names:
            if name in manifest.packs:
                # Uninstall entire pack
                for skill_name in manifest.packs[name]["skills"]:
                    for adapter in adapters:
                        install_dir = adapter.install_path(skill_name)
                        if install_dir.exists():
                            import shutil
                            shutil.rmtree(install_dir)
                            console.print(f"  [red]-[/red] {skill_name} from {adapter.display_name}")
                manifest.remove_pack(name)
            else:
                # Try individual skill
                for pack_name, pack_data in list(manifest.packs.items()):
                    if name in pack_data.get("skills", []):
                        for adapter in adapters:
                            install_dir = adapter.install_path(name)
                            if install_dir.exists():
                                import shutil
                                shutil.rmtree(install_dir)
                                console.print(f"  [red]-[/red] {name} from {adapter.display_name}")
                        pack_data["skills"].remove(name)
                        if not pack_data["skills"]:
                            manifest.remove_pack(pack_name)

        manifest.save()
        console.print("[green]Done.[/green]")

    @app.command()
    def platforms():
        """Show detected platforms and their install paths."""
        table = Table(title="Platform Detection")
        table.add_column("Platform")
        table.add_column("Detected")
        table.add_column("Slash Commands")
        table.add_column("Install Path")

        for adapter_cls in ALL_ADAPTERS:
            adapter = adapter_cls()
            detected = "[green]Yes[/green]" if adapter.is_available() else "[dim]No[/dim]"
            slash = "[green]Yes[/green]" if adapter.supports_slash_commands else "[dim]No[/dim]"
            table.add_row(adapter.display_name, detected, slash, str(adapter.install_path("example-skill")))

        console.print(table)

    return app


def main():
    app = create_app()
    app()
```

- [ ] **Step 4: Run tests**

```bash
PYTHONPATH=src:. python -m pytest tests/test_cli.py -v
```

Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/bb_skills_cli/__init__.py
git commit -m "feat: build bb-skills CLI with install, update, list, uninstall, platforms commands"
```

---

## Task 10: Write pyproject.toml

**Files:**
- Rewrite: `pyproject.toml`

- [ ] **Step 1: Write new pyproject.toml**

```toml
[project]
name = "bb-skills-cli"
version = "1.0.0"
description = "Install and manage BB-Skills — AI coding skills enriched with BuildBetter customer evidence."
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "BuildBetter", email = "eng@buildbetter.app" },
]
keywords = ["ai", "skills", "claude", "codex", "buildbetter", "spec-driven"]

[project.urls]
Homepage = "https://github.com/buildbetter-app/BB-Skills"
Repository = "https://github.com/buildbetter-app/BB-Skills"
Issues = "https://github.com/buildbetter-app/BB-Skills/issues"

[project.scripts]
bb-skills = "bb_skills_cli:main"

[project.dependencies]
typer = ">=0.9"
rich = ">=13.0"
httpx = ">=0.24"
pyyaml = ">=6.0"
packaging = ">=23.0"

[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/bb_skills_cli", "adapters", "skills", "scripts", "templates"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.coverage.run]
source = ["src", "adapters"]
omit = ["*/tests/*", "*/__pycache__/*"]
```

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "feat: rewrite pyproject.toml for bb-skills-cli package"
```

---

## Task 11: Write README, LICENSE, CONTRIBUTING, CHANGELOG

**Files:**
- Rewrite: `README.md`
- Modify: `LICENSE`
- Rewrite: `CONTRIBUTING.md`
- Rewrite: `CHANGELOG.md`

- [ ] **Step 1: Write new README.md**

Write `README.md` following the structure from the spec: hero, what is this, quick start, available packs, platform support matrix, skill reference, BuildBetter integration, updating, contributing, acknowledgments, license. Keep it concise — under 300 lines total.

- [ ] **Step 2: Update LICENSE**

Add to the top of the existing MIT LICENSE file:

```
Copyright (c) 2026 BuildBetter, Inc.
Portions copyright (c) GitHub, Inc. (github/spec-kit)

Permission is hereby granted...
[rest of MIT license]
```

- [ ] **Step 3: Write CONTRIBUTING.md**

Brief guide: how to add a new skill, how to add a new adapter, how to test, PR guidelines. Under 100 lines.

- [ ] **Step 4: Write CHANGELOG.md**

```markdown
# Changelog

## 1.0.0 (2026-04-XX)

### New
- Skills-first architecture with pack-based installation
- 3 skill packs: core, spec-workflow (9 skills), testing (3 skills)
- Multi-platform support: Claude Code, Codex, Cursor, Copilot, Gemini, Windsurf, Amazon Q
- `bb-skills` CLI for install, update, list, uninstall, platforms
- User-initiated update checking via GitHub releases

### Acknowledgments
- Spec-workflow skills derived from [github/spec-kit](https://github.com/github/spec-kit) (MIT)
- Extended with BuildBetter customer evidence integration
```

- [ ] **Step 5: Commit**

```bash
git add README.md LICENSE CONTRIBUTING.md CHANGELOG.md
git commit -m "docs: new README, updated LICENSE, CONTRIBUTING, and CHANGELOG"
```

---

## Task 12: Remove old spec-kit files

**Files:**
- Delete: all files listed in the "Files to delete" section above

- [ ] **Step 1: Remove old source and extensions**

```bash
cd <repo-root>
rm -rf src/specify_cli/
rm -rf extensions/
```

- [ ] **Step 2: Remove old templates/commands (now in skills/)**

```bash
rm -rf templates/commands/
rm -f templates/agent-file-template.md
rm -f templates/vscode-settings.json
```

- [ ] **Step 3: Remove old scripts (keeping BuildBetter ones)**

```bash
rm -f scripts/bash/create-new-feature.sh
rm -f scripts/bash/setup-plan.sh
rm -f scripts/bash/check-prerequisites.sh
rm -f scripts/bash/common.sh
rm -f scripts/bash/update-agent-context.sh
rm -f scripts/powershell/create-new-feature.ps1
rm -f scripts/powershell/setup-plan.ps1
rm -f scripts/powershell/check-prerequisites.ps1
rm -f scripts/powershell/common.ps1
rm -f scripts/powershell/update-agent-context.ps1
```

- [ ] **Step 4: Remove old tests**

```bash
rm -f tests/test_ai_skills.py
rm -f tests/test_cursor_frontmatter.py
rm -f tests/test_extensions.py
```

- [ ] **Step 5: Remove old docs and misc files**

```bash
rm -rf docs/index.md docs/quickstart.md docs/installation.md docs/local-development.md
rm -rf docs/upgrade.md docs/README.md docs/toc.yml docs/docfx.json
rm -rf .github/
rm -rf logs/ media/ assets/
rm -f spec-driven.md AGENTS.md SUPPORT.md CODE_OF_CONDUCT.md SECURITY.md
rm -f spec-kit.code-workspace
```

- [ ] **Step 6: Commit removals**

```bash
git add -A
git commit -m "chore: remove spec-kit scaffolding and old CLI code

Drops extensions system (14,917 lines), old specify CLI (2,430 lines),
spec-kit-specific scripts, templates, and docs. All valuable content
has been migrated to the new skills/ directory structure."
```

---

## Task 13: Final verification and clean check

**Files:**
- All remaining files in the repo

- [ ] **Step 1: Verify directory structure matches spec**

```bash
cd <repo-root>
find . -not -path './.git/*' -not -path './__pycache__/*' -not -name '*.pyc' | sort
```

Verify the output matches the spec's repo structure.

- [ ] **Step 2: Run all tests**

```bash
PYTHONPATH=src:. python -m pytest tests/ -v
```

Expected: ALL PASS

- [ ] **Step 3: Check for secrets or sensitive data**

```bash
grep -r "api_key\|password\|secret\|token" --include="*.py" --include="*.md" --include="*.yml" --include="*.json" . | grep -v ".git/" | grep -v "node_modules/" | grep -v "__pycache__/"
```

Verify no actual secrets are committed — only references to environment variables like `BUILDBETTER_API_KEY`.

- [ ] **Step 4: Check for stale spec-kit references**

```bash
grep -r "spec-kit\|spec_kit\|speckit\|specify_cli\|github/spec-kit" --include="*.py" --include="*.md" --include="*.yml" --include="*.toml" . | grep -v ".git/" | grep -v "docs/superpowers/"
```

Only allowed references: acknowledgments in README, LICENSE, CHANGELOG, and the design spec.

- [ ] **Step 5: Verify CLI can run**

```bash
cd <repo-root>
PYTHONPATH=src python -m bb_skills_cli --help
```

Expected: shows help with install, update, list, uninstall, platforms commands.

- [ ] **Step 6: Test a local install**

```bash
PYTHONPATH=src python -m bb_skills_cli install testing --platform claude
```

Verify skills appear in `~/.claude/skills/app-navigator/`, etc.

- [ ] **Step 7: Verify the install works**

```bash
ls -la ~/.claude/skills/app-navigator/
ls -la ~/.claude/skills/trust-but-verify/
ls -la ~/.claude/skills/generate-tests/
```

- [ ] **Step 8: Final commit if any fixes needed**

```bash
git status
# Fix anything, then:
git add -A
git commit -m "fix: final cleanup before initial release"
```

- [ ] **Step 9: Verify clean git status**

```bash
git status
git log --oneline -15
```

Should show a clean working tree and a clear commit history on the `restructure/skills-first` branch.

---

## Summary

| Task | Description | Commits |
|------|------------|---------|
| 1 | Directory structure + .gitignore | 1 |
| 2 | Pack definitions | 1 |
| 3 | Convert 9 spec-workflow commands to SKILL.md | 1 |
| 4 | Copy 3 browser testing skills | 1 |
| 5 | Core bb-skills-update skill | 1 |
| 6 | Base adapter + Claude adapter (TDD) | 1 |
| 7 | Remaining 6 adapters (TDD) | 1 |
| 8 | Manifest module (TDD) | 1 |
| 9 | Full CLI (install, update, list, uninstall, platforms) | 1 |
| 10 | pyproject.toml | 1 |
| 11 | README, LICENSE, CONTRIBUTING, CHANGELOG | 1 |
| 12 | Remove old spec-kit files | 1 |
| 13 | Final verification + clean check | 0-1 |

**Total: ~13 commits, 13 tasks**
