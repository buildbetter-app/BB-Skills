"""Cursor adapter — converts SKILL.md to .mdc format."""

from pathlib import Path
from bb_skills_adapters.base import BaseAdapter, parse_skill_frontmatter


class CursorAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "cursor"

    @property
    def display_name(self) -> str:
        return "Cursor"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unnamed")
        description = metadata.get("description", "")

        # Build .mdc format with frontmatter
        parts = []
        parts.append("---")
        parts.append(f"description: {description}")
        parts.append("alwaysApply: true")
        parts.append("---")
        parts.append("")
        parts.append(body)

        # Append supporting files inline
        for filename, content in sorted(supporting_files.items()):
            parts.append("")
            parts.append(f"## Reference: {filename}")
            parts.append("")
            parts.append(content)

        output_filename = f"bb-skills-{skill_name}.mdc"
        return {output_filename: "\n".join(parts)}

    def install_path(self, skill_name: str) -> Path:
        return Path.cwd() / ".cursor" / "rules"

    def is_available(self) -> bool:
        return (Path.cwd() / ".cursor").is_dir()

    @property
    def supports_slash_commands(self) -> bool:
        return False

    @property
    def supports_multi_file(self) -> bool:
        return False
