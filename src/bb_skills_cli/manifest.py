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
        self.path.chmod(0o600)

    def add_pack(self, pack_name: str, skills: list[str]):
        self.packs[pack_name] = {"skills": skills}

    def remove_pack(self, pack_name: str):
        self.packs.pop(pack_name, None)

    def has_skill(self, skill_name: str) -> bool:
        for pack_data in self.packs.values():
            if skill_name in pack_data.get("skills", []):
                return True
        return False
