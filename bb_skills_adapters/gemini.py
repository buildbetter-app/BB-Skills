"""Gemini CLI adapter — converts SKILL.md to TOML command format."""

from pathlib import Path
from bb_skills_adapters.base import BaseAdapter, parse_skill_frontmatter


class GeminiAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Gemini CLI"

    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        metadata, body = parse_skill_frontmatter(skill_content)
        skill_name = metadata.get("name", "unnamed")
        description = metadata.get("description", "")

        # Build the prompt body with supporting files appended
        prompt_parts = [body]
        for filename, content in sorted(supporting_files.items()):
            prompt_parts.append("")
            prompt_parts.append(f"## Reference: {filename}")
            prompt_parts.append("")
            prompt_parts.append(content)

        prompt_body = "\n".join(prompt_parts)

        # Escape backslashes and triple quotes for TOML
        prompt_body = prompt_body.replace("\\", "\\\\")
        prompt_body = prompt_body.replace('"""', '\\"""')

        # Build TOML output
        lines = [
            f'description = "{description}"',
            f'prompt = """\n{prompt_body}\n"""',
        ]

        output_filename = f"{skill_name}.toml"
        return {output_filename: "\n".join(lines)}

    def install_path(self, skill_name: str) -> Path:
        return Path.home() / ".gemini" / "commands" / "bb-skills" / skill_name

    def is_available(self) -> bool:
        return (Path.home() / ".gemini").is_dir()

    @property
    def supports_slash_commands(self) -> bool:
        return True
