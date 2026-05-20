# Configuration

`sdd-plus-plus` is usable with zero config — every option has a sensible default. The config layer exists for two things:

1. Pointing sdd at a **shared findings wiki** so judgment calls stop being trapped in per-repo `.governance/findings/` folders.
2. Overriding defaults (tier, AI-resistance policy, validation strictness, MCP transport) per-user or per-repo without editing code.

The full option list lives in [`.governance/sdd-config.schema.yaml`](.governance/sdd-config.schema.yaml). A worked example with every option populated and commented lives in [`examples/sdd-config.example.yaml`](examples/sdd-config.example.yaml).

## Precedence

Sources are merged in this order — later sources override earlier ones:

1. **Built-in defaults** (whatever the schema declares as `default:`)
2. **Global user config** at `~/.config/sdd/config.yaml`
3. **Project config** at `.governance/config.yaml`
4. **Environment variables** prefixed `SDD_` (CI and plugin overrides)

Use the global file for things that follow *you* (your wiki repo, your assistance policy, your auth). Use the project file for things that follow *this codebase* (tier, governance directory if non-standard). Use env vars for ephemeral overrides — CI, sandboxes, debugging.

## Bootstrap

There is no `sdd config init` yet (planned — see ROADMAP v0.4). For now:

```bash
mkdir -p ~/.config/sdd
cp examples/sdd-config.example.yaml ~/.config/sdd/config.yaml
$EDITOR ~/.config/sdd/config.yaml
```

For per-project config:

```bash
cp examples/sdd-config.example.yaml .governance/config.yaml
$EDITOR .governance/config.yaml
```

Empty files are valid. Start minimal and add keys as you need them — every key not set falls back to the schema default.

## The wiki layer

The wiki is the part most users come to the config layer for.

**What it solves.** Per-repo findings are invisible outside that repo. Engineers in adjacent codebases re-derive the same judgment calls. A wiki repo turns findings into a shared knowledge layer the whole org reads from and writes to — and that AI assistants can `search_findings` against via the MCP server.

**How sync works.** When `wiki.repo` is set:

- On read (e.g. `sdd findings list`, `search_findings` MCP call) the local cache is refreshed from the remote — controlled by `sync_mode`.
- On write (e.g. `sdd findings add` followed by Dana's ingestion) the new finding is *staged* locally first. It only reaches the remote if `write_policy` permits — by default, `reviewer-only`, meaning Dana (or a human reviewer) is the gate.
- The local cache lives under `wiki.local_cache` (default `~/.cache/sdd/wiki`), with one sub-folder per wiki repo so multiple wikis can coexist.

**Sync modes.**

- `manual` — no automatic git operations. `sdd wiki pull` and `sdd wiki push` are the only commands that touch the cache.
- `auto-pull` (default) — fetch latest before every read. Pushes stay explicit so half-baked findings don't leak.
- `auto-sync` — fetch before reads, push after writes. Use only with a strict `write_policy` and high trust in your reviewer pipeline.

**Write policies.**

- `forbidden` — read-only. The wiki is a knowledge source, not a write target.
- `reviewer-only` (default) — only the Dana agent or a human reviewer may push. Matches the framework's intent: findings are reviewed before they cross the trust boundary.
- `any-author` — anyone with auth may push. Use only inside small, high-trust teams.

**Auth.** Tokens are never stored in the config file. The config stores the *name* of the env var that holds the token:

```yaml
wiki:
  auth:
    method: https-token
    token_env_var: SDD_WIKI_TOKEN
```

Then export the token in your shell or CI:

```bash
export SDD_WIKI_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

For SSH-based access, `method: ssh` is the default and uses your normal git SSH identity. Override `ssh_key_path` only if you have a dedicated wiki key.

## Environment variables

Every config field can be overridden with an env var prefixed `SDD_`. Nested keys use double underscores. Some commonly used ones:

| Variable | Overrides |
|---|---|
| `SDD_CONFIG` | Path to an additional config file, applied with higher precedence than the global and project files. |
| `SDD_TIER` | `tier` |
| `SDD_WIKI_REPO` | `wiki.repo` |
| `SDD_WIKI_BRANCH` | `wiki.branch` |
| `SDD_WIKI_SYNC_MODE` | `wiki.sync_mode` |
| `SDD_WIKI_WRITE_POLICY` | `wiki.write_policy` |
| `SDD_WIKI_TOKEN` | The token itself (read when `auth.method` is `https-token`) |
| `SDD_MCP_TRANSPORT` | `mcp.transport` |
| `SDD_VALIDATION_STRICT` | `validation.strict_mode` (`true` / `false`) |

The plugin manifest passes a curated subset of these into the `sdd serve` MCP server so a user can change wiki settings from their shell without editing config files.

## Inspecting the active config

Once `/sdd-config` is wired (see `commands/sdd-config.md`), invoking it in Claude Code will:

- Show the merged config from all sources
- Indicate which source supplied each value (default / global / project / env)
- Validate against the schema and surface any errors
- Surface missing-but-likely-wanted settings (e.g. `wiki.repo` not set on a repo that's clearly part of a multi-repo org)

From the CLI directly:

```bash
sdd config show       # planned — print effective config
sdd config validate   # planned — validate against the schema
sdd config sources    # planned — show which source set each key
```

These are v0.4 work. Until they ship, `cat ~/.config/sdd/config.yaml` and `cat .governance/config.yaml` are the reference.

## Security notes

- **Tokens never go in the config file.** The schema enforces this — only env-var *names* are stored. If you find yourself wanting to paste a token in directly, that's a sign to use SSH or a secrets manager.
- **`.governance/config.yaml` is committed.** Treat it as you would `package.json` — review it on every PR. Project config is intentionally checked in so the whole team gets the same defaults.
- **The wiki repo can carry secrets too.** Findings sometimes describe sensitive trade-offs (security boundaries, third-party limits, customer-specific behavior). Use a private wiki repo if your findings risk exposing more than you'd put in a public engineering blog.
- **`auto-sync` + `any-author` is dangerous together.** A confused agent or accidental edit could leak unreviewed findings to the org-wide wiki. Don't combine these unless you know exactly what you're doing.

## Migrating an existing repo

If you already have `.governance/findings/` in this repo and want to migrate them to a wiki:

1. Set `wiki.repo` in `.governance/config.yaml`.
2. Run `sdd wiki init` (planned v0.4) to clone the wiki to the local cache.
3. Run `sdd wiki migrate-local` (planned v0.4) to copy local findings to the cache under `path_prefix/`, leaving the local copies in place.
4. Have Dana review the migrated findings — duplicates, missing `linked_capability` fields, contradicting prior findings.
5. `sdd wiki push` (planned v0.4) to publish.

Until those commands ship, the migration is manual: `cp` the files into your cloned wiki, commit, push.
