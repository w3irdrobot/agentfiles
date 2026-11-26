#!/usr/bin/env python3
"""Install shared instructions, skills, and MCP servers for selected tools."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / "skills"
INSTRUCTIONS = ROOT / "instructions/AGENTS.md"
MCP_SERVERS = ROOT / "mcp/servers.json"
TOOLS = ("maple", "codex", "claude", "opencode")


def links(home, tools=("maple",)):
    if not tools or len(set(tools)) != len(tools) or any(tool not in TOOLS for tool in tools):
        raise ValueError("Select unique tools from: " + ", ".join(TOOLS))
    names = sorted(path.name for path in SKILLS.iterdir()
                   if path.is_dir() and not path.name.startswith(".")
                   and (path / "SKILL.md").is_file())
    if not names:
        raise ValueError("No skills found under skills/")
    result = [(home / ".agents/AGENTS.md", INSTRUCTIONS)]
    instruction_paths = {
        "codex": ".codex/AGENTS.md",
        "claude": ".claude/CLAUDE.md",
        "opencode": ".config/opencode/AGENTS.md",
    }
    for tool in tools:
        if tool in instruction_paths:
            result.append((home / instruction_paths[tool], INSTRUCTIONS))
    for name in names:
        source = SKILLS / name
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing skill: {name}")
        result.append((home / ".agents/skills" / name, source))
        if "claude" in tools:
            result.append((home / ".claude/skills" / name, source))
        if "opencode" in tools:
            # Keep explicit discovery working when external skill discovery is off.
            result.append((home / ".config/opencode/skills" / name, source))
    return result


def owned_link(destination, source):
    return (destination.is_symlink() and destination.exists()
            and destination.resolve() == source.resolve())


def preflight(home, plan):
    if not home.is_dir():
        raise ValueError(f"Target home must already exist: {home}")
    for destination, source in plan:
        if not source.exists():
            raise ValueError(f"Missing source: {source}")
        for parent in destination.parents:
            if parent == home:
                break
            if parent.is_symlink() or parent.exists() and not parent.is_dir():
                raise ValueError(f"Conflicting parent: {parent}")
        if os.path.lexists(destination):
            if owned_link(destination, source) or destination.resolve() == source.resolve():
                continue
            raise ValueError(f"Conflict: {destination}; move it manually after review")
        if any(parent.is_symlink() for parent in destination.parents if parent != home):
            raise ValueError(f"Refusing to create files through a linked parent: {destination}")


def mcp_registrations(home, tools):
    if "codex" not in tools and "claude" not in tools:
        return []
    servers = json.loads(MCP_SERVERS.read_text())
    registrations = []
    for tool in ("codex", "claude"):
        if tool not in tools:
            continue
        env = {**os.environ, "HOME": str(home)}
        if tool == "codex":
            try:
                import tomllib
            except ModuleNotFoundError:
                raise ValueError("Codex MCP registration requires Python 3.11 or newer") from None

            config = home / ".codex/config.toml"
            env["CODEX_HOME"] = str(config.parent)
            config_format = tomllib
            server_key = "mcp_servers"
        else:
            config_dir = Path(env["CLAUDE_CONFIG_DIR"]) if env.get("CLAUDE_CONFIG_DIR") else home
            config = config_dir / ".claude.json"
            config_format = json
            server_key = "mcpServers"

        try:
            settings = config_format.loads(config.read_text())
            existing = settings.get(server_key, {}) if isinstance(settings, dict) else None
        except FileNotFoundError:
            existing = {}
        except ValueError:
            raise ValueError(f"Could not parse MCP settings in {config}") from None
        if not isinstance(existing, dict):
            raise ValueError(f"Expected MCP settings to be a table in {config}")

        for name, url in servers.items():
            if name in existing:
                print(f"Keeping existing MCP server {name} in {config}")
                continue
            if config.is_symlink() or config.parent.is_symlink():
                raise ValueError(f"Register {name} manually in linked config {config}")
            executable = shutil.which(tool)
            if executable is None:
                raise ValueError(f"Install {tool} to register {name}, or use --skip-mcp")
            if tool == "codex":
                args = ["mcp", "add", name, "--url", url]
            else:
                args = ["mcp", "add", "--transport", "http", "--scope", "user", name, url]
            registrations.append((name, config, [executable, *args], env))
    return registrations


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="For Paseo, run on the daemon host and select the providers it launches.",
    )
    parser.add_argument("--home", type=Path, default=Path.home(),
                        help="existing target home (default: current user's home)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-mcp", action="store_true", help="only link instructions and skills")
    parser.add_argument("--tools", required=True,
                        help="comma-separated selection: " + ",".join(TOOLS))
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    try:
        tools = tuple(args.tools.split(","))
        config_variables = {"codex": "CODEX_HOME", "claude": "CLAUDE_CONFIG_DIR",
                            "opencode": "XDG_CONFIG_HOME"}
        for variable in (config_variables[tool] for tool in tools if tool in config_variables):
            if os.environ.get(variable):
                expected = {"CODEX_HOME": home / ".codex",
                            "CLAUDE_CONFIG_DIR": home / ".claude",
                            "XDG_CONFIG_HOME": home / ".config"}[variable]
                if Path(os.environ[variable]).expanduser().resolve() != expected:
                    raise ValueError(f"Custom {variable} is unsupported; use the tool's default layout")
        if "codex" in tools and os.path.lexists(home / ".codex/AGENTS.override.md"):
            raise ValueError("Codex AGENTS.override.md would shadow shared instructions; review it first")
        plan = links(home, tools)
        preflight(home, plan)
        registrations = [] if args.skip_mcp else mcp_registrations(home, tools)
        for destination, source in plan:
            if destination.exists() and destination.resolve() == source.resolve():
                print(f"Already linked: {destination}")
                continue
            if args.dry_run:
                print(f"Would link: {destination} -> {source}")
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.symlink_to(os.path.relpath(source, destination.parent),
                                       target_is_directory=source.is_dir())
                print(f"Linked: {destination} -> {source}")
        for name, config, command, env in registrations:
            if args.dry_run:
                print(f"Would register MCP server {name} in {config}")
                continue
            result = subprocess.run(command, env=env, capture_output=True)
            if result.returncode:
                raise ValueError(f"Could not register MCP server {name} in {config} (exit {result.returncode})")
            print(f"Registered MCP server {name} in {config}")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"agentfiles: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
