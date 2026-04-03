"""Platform adapters for converting SKILL.md to target formats."""

from bb_skills_adapters.base import BaseAdapter, parse_skill_frontmatter, read_skill_directory
from bb_skills_adapters.claude import ClaudeAdapter
from bb_skills_adapters.codex import CodexAdapter
from bb_skills_adapters.cursor import CursorAdapter
from bb_skills_adapters.copilot import CopilotAdapter
from bb_skills_adapters.gemini import GeminiAdapter
from bb_skills_adapters.windsurf import WindsurfAdapter
from bb_skills_adapters.amazon_q import AmazonQAdapter

ALL_ADAPTERS = [
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    CopilotAdapter,
    GeminiAdapter,
    WindsurfAdapter,
    AmazonQAdapter,
]
