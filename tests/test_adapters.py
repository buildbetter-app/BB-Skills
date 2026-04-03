"""Tests for platform adapters."""

import pytest
from pathlib import Path
from bb_skills_adapters.base import BaseAdapter, parse_skill_frontmatter


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


from bb_skills_adapters.claude import ClaudeAdapter


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
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Codex adapter tests
# ---------------------------------------------------------------------------
from bb_skills_adapters.codex import CodexAdapter


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
        assert path == Path.home() / ".codex" / "skills" / "trust-but-verify"

    def test_is_available(self):
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Cursor adapter tests
# ---------------------------------------------------------------------------
from bb_skills_adapters.cursor import CursorAdapter


class TestCursorAdapter:
    def setup_method(self):
        self.adapter = CursorAdapter()

    def test_name(self):
        assert self.adapter.name == "cursor"
        assert self.adapter.display_name == "Cursor"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_supports_multi_file(self):
        assert self.adapter.supports_multi_file is False

    def test_convert_produces_mdc(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill

Do the thing."""
        supporting = {"helper.md": "# Helper content"}
        result = self.adapter.convert(skill, supporting)
        assert len(result) == 1
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test-skill.mdc"
        content = result[filename]
        assert "alwaysApply: true" in content
        assert "description:" in content
        assert "# Test Skill" in content
        assert "## Reference: helper.md" in content
        assert "# Helper content" in content

    def test_convert_no_supporting_files(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill"""
        result = self.adapter.convert(skill, {})
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test-skill.mdc"
        content = result[filename]
        assert "## Reference:" not in content

    def test_install_path(self):
        path = self.adapter.install_path("test-skill")
        assert ".cursor" in str(path)
        assert "rules" in str(path)

    def test_is_available(self):
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Copilot adapter tests
# ---------------------------------------------------------------------------
from bb_skills_adapters.copilot import CopilotAdapter


class TestCopilotAdapter:
    def setup_method(self):
        self.adapter = CopilotAdapter()

    def test_name(self):
        assert self.adapter.name == "copilot"
        assert self.adapter.display_name == "GitHub Copilot"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_convert_strips_frontmatter(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill

Do the thing."""
        supporting = {"helper.md": "# Helper content"}
        result = self.adapter.convert(skill, supporting)
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test-skill.instructions.md"
        content = result[filename]
        assert "---" not in content
        assert "name: test-skill" not in content
        assert "# Test Skill" in content
        assert "## Reference: helper.md" in content
        assert "# Helper content" in content

    def test_convert_no_supporting_files(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill"""
        result = self.adapter.convert(skill, {})
        content = list(result.values())[0]
        assert "## Reference:" not in content

    def test_install_path(self):
        path = self.adapter.install_path("test-skill")
        assert ".github" in str(path)
        assert "instructions" in str(path)

    def test_is_available(self):
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Gemini adapter tests
# ---------------------------------------------------------------------------
from bb_skills_adapters.gemini import GeminiAdapter


class TestGeminiAdapter:
    def setup_method(self):
        self.adapter = GeminiAdapter()

    def test_name(self):
        assert self.adapter.name == "gemini"
        assert self.adapter.display_name == "Gemini CLI"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is True

    def test_convert_produces_toml(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill

Do the thing."""
        supporting = {"helper.md": "# Helper content"}
        result = self.adapter.convert(skill, supporting)
        filename = list(result.keys())[0]
        assert filename == "test-skill.toml"
        content = result[filename]
        assert 'description = "A test skill"' in content
        assert 'prompt = """' in content
        assert "# Test Skill" in content
        assert "## Reference: helper.md" in content

    def test_convert_escapes_backslashes(self):
        skill = "---\nname: test-skill\ndescription: A test skill\n---\n\nUse a backslash: \\ here"
        result = self.adapter.convert(skill, {})
        content = list(result.values())[0]
        # Backslashes in the body should be escaped for TOML
        assert "\\\\" in content

    def test_install_path(self):
        path = self.adapter.install_path("test-skill")
        assert path == Path.home() / ".gemini" / "commands" / "bb-skills" / "test-skill"

    def test_is_available(self):
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Windsurf adapter tests
# ---------------------------------------------------------------------------
from bb_skills_adapters.windsurf import WindsurfAdapter


class TestWindsurfAdapter:
    def setup_method(self):
        self.adapter = WindsurfAdapter()

    def test_name(self):
        assert self.adapter.name == "windsurf"
        assert self.adapter.display_name == "Windsurf"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_convert_strips_frontmatter(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill

Do the thing."""
        supporting = {"helper.md": "# Helper content"}
        result = self.adapter.convert(skill, supporting)
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test-skill.md"
        content = result[filename]
        assert "---" not in content
        assert "name: test-skill" not in content
        assert "# Test Skill" in content
        assert "## Reference: helper.md" in content
        assert "# Helper content" in content

    def test_convert_no_supporting_files(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill"""
        result = self.adapter.convert(skill, {})
        content = list(result.values())[0]
        assert "## Reference:" not in content

    def test_install_path(self):
        path = self.adapter.install_path("test-skill")
        assert ".windsurf" in str(path)
        assert "rules" in str(path)

    def test_is_available(self):
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Amazon Q adapter tests
# ---------------------------------------------------------------------------
from bb_skills_adapters.amazon_q import AmazonQAdapter


class TestAmazonQAdapter:
    def setup_method(self):
        self.adapter = AmazonQAdapter()

    def test_name(self):
        assert self.adapter.name == "amazon-q"
        assert self.adapter.display_name == "Amazon Q Developer"

    def test_supports_slash_commands(self):
        assert self.adapter.supports_slash_commands is False

    def test_convert_strips_frontmatter(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill

Do the thing."""
        supporting = {"helper.md": "# Helper content"}
        result = self.adapter.convert(skill, supporting)
        filename = list(result.keys())[0]
        assert filename == "bb-skills-test-skill.md"
        content = result[filename]
        assert "---" not in content
        assert "name: test-skill" not in content
        assert "# Test Skill" in content
        assert "## Reference: helper.md" in content
        assert "# Helper content" in content

    def test_convert_no_supporting_files(self):
        skill = """---
name: test-skill
description: A test skill
---

# Test Skill"""
        result = self.adapter.convert(skill, {})
        content = list(result.values())[0]
        assert "## Reference:" not in content

    def test_install_path(self):
        path = self.adapter.install_path("test-skill")
        assert ".amazonq" in str(path)
        assert "rules" in str(path)

    def test_is_available(self):
        result = self.adapter.is_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# ALL_ADAPTERS registry test
# ---------------------------------------------------------------------------
class TestAdapterRegistry:
    def test_all_adapters_list(self):
        from bb_skills_adapters import ALL_ADAPTERS
        assert len(ALL_ADAPTERS) == 7
        names = [a().name for a in ALL_ADAPTERS]
        assert "claude" in names
        assert "codex" in names
        assert "cursor" in names
        assert "copilot" in names
        assert "gemini" in names
        assert "windsurf" in names
        assert "amazon-q" in names
