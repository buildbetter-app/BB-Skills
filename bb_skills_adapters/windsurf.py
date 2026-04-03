"""Windsurf adapter — strips frontmatter, outputs plain markdown."""

from pathlib import Path
from bb_skills_adapters.base import BaseAdapter, parse_skill_frontmatter


class WindsurfAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "windsurf"

    @property
    def display_name(self) -> str:
        return "Windsurf"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unnamed")

        parts = [body]

        # Append supporting files with reference headers
        for filename, content in sorted(supporting_files.items()):
            parts.append("")
            parts.append(f"## Reference: {filename}")
            parts.append("")
            parts.append(content)

        output_filename = f"bb-skills-{skill_name}.md"
        return {output_filename: "\n".join(parts)}

    def install_path(self, skill_name: str) -> Path:
        return Path.cwd() / ".windsurf" / "rules"

    def is_available(self) -> bool:
        return (Path.cwd() / ".windsurf").is_dir()

    @property
    def supports_slash_commands(self) -> bool:
        return False
