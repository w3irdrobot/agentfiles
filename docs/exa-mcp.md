# Exa MCP

Use Exa's hosted Streamable HTTP endpoint, `https://mcp.exa.ai/mcp`. Search and
page fetching work without an account or API key, subject to Exa's free rate
limits. Configure each client on the machine and under the user that runs it.
[Exa MCP docs](https://exa.ai/docs/get-started/exa-mcp)

## Connect the clients

`link.py` reads [mcp/servers.json](../mcp/servers.json) and registers Exa for
Claude Code and Codex when selected. Each CLI writes its own user config so it
can keep managing its settings. Existing server entries with the same name are
kept. To preview the config changes, run:

```bash
./link.py --tools claude,codex --dry-run
```

Run without `--dry-run` to apply. For a manual registration, use the client
instructions below.

- **Claude Code** — Register the server for your user across projects.

  ```bash
  claude mcp add --transport http --scope user exa https://mcp.exa.ai/mcp
  ```

  [Claude Code MCP docs](https://code.claude.com/docs/en/mcp)
- **Codex** — Register the server in your user config.

  ```bash
  codex mcp add exa --url https://mcp.exa.ai/mcp
  ```

  [Codex MCP docs](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

Use a fresh task in each client and ask it to search for official Git worktree
documentation. Check the tool call for `web_search_exa`. The `/mcp` command
also shows the server.

## Prefer Exa for web search

The linked shared instructions prefer Exa in Claude Code and Codex, with other
web tools available as a fallback. To disable built-in search, first verify Exa
works.

- **Claude Code** — Add `"WebSearch"` to `permissions.deny` in
  `~/.claude/settings.json`, preserving existing entries.
  [Claude Code permissions](https://code.claude.com/docs/en/permissions)
- **Codex** — Set the top-level `web_search = "disabled"` in
  `~/.codex/config.toml` (or `$CODEX_HOME/config.toml`). Put it before the first
  TOML table if the setting is absent.
  [Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference)

## If keyless access falls short

Exa requires a direct IPv4 connection for keyless access. If the host gets a 403
over IPv6 or through a proxy, or hits the free rate limit, Exa offers browser
sign-in at `https://mcp.exa.ai/mcp?login`. OAuth keeps credentials out of this
repo, but clients may persist tokens locally. For keyed use in Claude Code or
Codex, a secret manager can inject `EXA_API_KEY` into the client process at
launch. Reference `${EXA_API_KEY}` as the Claude Code `x-api-key` header value,
or set `env_http_headers = { "x-api-key" = "EXA_API_KEY" }` in Codex's
`[mcp_servers.exa]` table.
[Exa authentication](https://exa.ai/docs/get-started/exa-mcp#authentication)
