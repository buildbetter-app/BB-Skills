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

    return skill_content, supporting


class BaseAdapter(ABC):
    """Base class for platform adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        ...

    @abstractmethod
    def convert(self, skill_content: str, supporting_files: dict[str, str]) -> dict[str, str]:
        ...

    @abstractmethod
    def install_path(self, skill_name: str) -> Path:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @property
    def supports_slash_commands(self) -> bool:
        return False

    @property
    def supports_multi_file(self) -> bool:
        return False
