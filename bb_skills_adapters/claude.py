"""Claude Code adapter — SKILL.md passthrough with multi-file support."""

from pathlib import Path
from bb_skills_adapters.base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "claude"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
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
