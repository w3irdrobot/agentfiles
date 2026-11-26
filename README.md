# Agentfiles

My shared instructions and skills for coding agents (Claude Code, Codex,
OpenCode, Maple), plus tooling for the machines they run on. It works the same
on my workstation and on worker nodes, and doesn't depend on my dotfiles.

```text
instructions/AGENTS.md   # Global rules every tool reads
skills/                  # One directory per skill, each with a SKILL.md
link.py                  # Links the above into each tool's home
SETUP.md                 # Workflow for an agent deploying this to a node
examples/node.md         # Template for per-machine guidance
scripts/, docs/, tests/  # Worker-node tooling (node-cleanup, cargo-metrics)
```

## Install

Clone it somewhere stable and link the tools that machine uses. For Paseo, run
the linker on the daemon host as the user that runs its providers. Select those
providers in `--tools`. This example configures Codex and Claude Code for Paseo
and keeps OpenCode's native links available. [Paseo provider docs](https://paseo.sh/docs/providers.md)

```bash
git clone git@github.com:w3irdrobot/agentfiles.git ~/projects/github.com/w3irdrobot/agentfiles
cd ~/projects/github.com/w3irdrobot/agentfiles
./link.py --tools codex,claude,opencode --dry-run
./link.py --tools codex,claude,opencode
```

Pick only the tools a machine actually runs; a worker might be just
`--tools maple,codex`. Run it as the user that runs the agents. Links point into
this checkout, so editing a skill or the instructions is live immediately; keep
the checkout where it is. Rerun `link.py` after adding a skill.

To have an agent deploy this to a worker node, point it at [SETUP.md](SETUP.md)
or the `deploy-agent-config` skill.

## Where things land

| Tool | Instructions | Skills |
| --- | --- | --- |
| Maple | `~/.agents/AGENTS.md` | `~/.agents/skills/<name>` |
| Codex | `~/.codex/AGENTS.md` | `~/.agents/skills/<name>` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills/<name>` |
| OpenCode | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/skills/<name>` |

`~/.agents` is always linked. Skills are linked one by one, so skills other
installers put in those directories stay put.

## How link.py behaves

- It never replaces a regular file, a foreign link, or a dangling link; it
  reports the conflict and stops. Move the file aside after reviewing it, then
  rerun. Existing correct links are left alone, so reruns are safe.
- It refuses custom `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, or `XDG_CONFIG_HOME`
  locations, and a Codex `AGENTS.override.md`, which would shadow the shared
  instructions.
- It doesn't prune. Deleting a skill here leaves its old links dangling; remove
  them by hand.
- `--home /some/test-home` rehearses against a scratch home.

## Per-machine guidance

Optional, non-secret notes for a specific machine go in
`~/.config/agent-config/node.md`; start from [examples/node.md](examples/node.md).
The shared instructions tell agents to read it. It's guidance, not config, so
check in a fresh session that the agent actually read it.

## Updating a worker

Pulling new commits into a linked checkout deploys them. Check the checkout's
status first, fast-forward only, and never reset or stash a node's local edits.
Then rerun `link.py --dry-run` and `link.py` to pick up new skills. After
deploying, start a fresh session in each tool and confirm the instructions and
skills loaded. In Paseo, check the skill suggestions in the composer for each
provider you use. In standalone Claude Code, use `/context` and `/skills`.

## Worker-node tooling

- [docs/node-build-metrics.md](docs/node-build-metrics.md): node-cleanup reports
  and Cargo build metrics, and where they're installed on a node.
- [docs/cargo-metrics.md](docs/cargo-metrics.md): installing the Cargo/Nix
  wrapper.
- Tests: `python3 -m unittest discover -s tests -v`.
