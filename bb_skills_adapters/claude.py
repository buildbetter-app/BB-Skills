"""Claude Code adapter — SKILL.md passthrough with multi-file support."""

import json
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

    def settings_path(self) -> Path:
        return Path.home() / ".claude" / "settings.json"

    def _load_settings(self) -> dict:
        path = self.settings_path()
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_settings(self, settings: dict) -> None:
        path = self.settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    def get_missing_mcp_servers(self, required: dict[str, dict]) -> dict[str, dict]:
        settings = self._load_settings()
        existing = settings.get("mcpServers", {})
        return {name: config for name, config in required.items() if name not in existing}

    def add_mcp_servers(self, servers: dict[str, dict]) -> None:
        settings = self._load_settings()
        mcp = settings.setdefault("mcpServers", {})
        for name, config in servers.items():
            if name not in mcp:
                mcp[name] = config
        self._save_settings(settings)
