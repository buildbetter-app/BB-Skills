"""BB-Skills CLI — install, update, and manage AI coding skills."""

__version__ = "1.0.0"

import shutil
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

from bb_skills_adapters import ALL_ADAPTERS, read_skill_directory
from bb_skills_adapters.base import parse_skill_frontmatter

console = Console()

GITHUB_REPO = "buildbetter-app/BB-Skills"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _find_skills_dir() -> Path:
    """Find the skills/ directory — local clone or downloaded."""
    local = _project_root / "skills"
    if local.is_dir():
        return local
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
    return [cls() for cls in ALL_ADAPTERS if cls().is_available()]


def _install_skill(skill_dir: Path, adapter, skill_name: str) -> Path:
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
            return _dedupe(targets)

        if name in packs:
            pack_data = packs[name]
            for dep in pack_data.get("dependencies", []):
                if dep in packs:
                    for skill_name in packs[dep].get("skills", []):
                        skill_path = skills_dir / dep / skill_name
                        if skill_path.is_dir():
                            targets.append((dep, skill_name, skill_path))
            for skill_name in pack_data.get("skills", []):
                skill_path = skills_dir / name / skill_name
                if skill_path.is_dir():
                    targets.append((name, skill_name, skill_path))
            continue

        pack_name = _find_skill_pack(name, packs)
        if pack_name:
            skill_path = skills_dir / pack_name / name
            if skill_path.is_dir():
                if "core" in packs and pack_name != "core":
                    for core_skill in packs["core"].get("skills", []):
                        core_path = skills_dir / "core" / core_skill
                        if core_path.is_dir():
                            targets.append(("core", core_skill, core_path))
                targets.append((pack_name, name, skill_path))
            continue

        console.print(f"[red]Unknown pack or skill: {name}[/red]")

    return _dedupe(targets)


def _dedupe(targets: list[tuple[str, str, Path]]) -> list[tuple[str, str, Path]]:
    """Deduplicate targets while preserving order."""
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
        platform: Optional[str] = typer.Option(None, help="Target platform(s), comma-separated (auto-detect if omitted)"),
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

        manifest.version = __version__
        manifest.platforms = sorted({a.name for a in adapters})
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
        if not available and not installed:
            available = True

        if available:
            packs = _discover_packs(resolved_skills_dir)
            table = Table(title="Available Packs & Skills")
            table.add_column("Pack", style="bold")
            table.add_column("Skill")
            table.add_column("Description")

            for pack_name, pack_data in packs.items():
                first = True
                for skill_name in pack_data.get("skills", []):
                    skill_file = resolved_skills_dir / pack_name / skill_name / "SKILL.md"
                    desc = ""
                    if skill_file.exists():
                        meta, _ = parse_skill_frontmatter(skill_file.read_text(encoding="utf-8"))
                        desc = meta.get("description", "")[:80]
                    pack_label = f"{pack_name} ({pack_data.get('display_name', '')})" if first else ""
                    table.add_row(pack_label, skill_name, desc)
                    first = False

            console.print(table)

        if installed:
            manifest = Manifest()
            if not manifest.packs:
                console.print("[yellow]No skills installed. Run: bb-skills install <pack>[/yellow]")
                return
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

        adapters = [cls() for cls in ALL_ADAPTERS if cls().name in manifest.platforms]

        for name in names:
            if name in manifest.packs:
                for skill_name in manifest.packs[name]["skills"]:
                    for adapter in adapters:
                        install_dir = adapter.install_path(skill_name)
                        if install_dir.exists():
                            shutil.rmtree(install_dir)
                            console.print(f"  [red]-[/red] {skill_name} from {adapter.display_name}")
                manifest.remove_pack(name)
            else:
                for pack_name, pack_data in list(manifest.packs.items()):
                    if name in pack_data.get("skills", []):
                        for adapter in adapters:
                            install_dir = adapter.install_path(name)
                            if install_dir.exists():
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
