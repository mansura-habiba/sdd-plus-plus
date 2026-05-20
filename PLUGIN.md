# Using sdd-plus-plus as a Claude Code plugin

This file is the install + usage guide for the plugin form of `sdd-plus-plus`. For the Python CLI, see `README.md`.

## Prerequisites

The plugin's MCP server invokes the `sdd` binary directly. Install it first:

```bash
pip install 'sdd-plus-plus[serve]'
sdd --version    # confirm it's on $PATH
```

If `sdd` is not on `$PATH`, the `sdd-governance` MCP server in the plugin will fail to start.

## Install the plugin

From inside Claude Code:

```text
/plugin marketplace add built-it-here/sdd-plus-plus
/plugin install sdd-plus-plus@sdd-plus-plus-marketplace
```

The first command registers this repo as a marketplace by reading `.claude-plugin/marketplace.json` from the default branch. The second installs the `sdd-plus-plus` plugin from that marketplace.

To confirm the install:

```text
/plugin list
```

You should see `sdd-plus-plus` enabled with two agents (`bob-scaffolder`, `dana-reviewer`), six commands, and one MCP server (`sdd-governance`).

## What you get

### Agents

Invoke by mention:

- **`@bob-scaffolder`** — scaffolds a new capability bundle (capability spec + acceptance YAML + task card + optional finding stub + todo list) in one pass. Use when starting any new unit of work.
- **`@dana-reviewer`** — peer-reviews a task card against the framework's contracts, ingests findings, and updates status. Use when a task card moves to `review`.

The two agents are designed to hand off to each other. Bob never edits production code; Dana never authors new artifacts.

### Slash commands

| Command | Purpose |
|---|---|
| `/sdd-init` | Bootstrap `.governance/`, `AGENTS.md`, `.github/` templates, and contract tests in the current repo. Accepts `--tier solo` (default) or `--tier team`. |
| `/sdd-validate` | Run `sdd validate` and surface schema or cross-reference errors. |
| `/sdd-doctor` | Run the 8-milestone adoption diagnostic; report what's complete and what's missing. |
| `/sdd-finding-add` | Record a finding. Pushes back if `consequences` are vague. Hands off to Dana for ingestion. |
| `/sdd-review <task-id>` | Open a structured peer review on a task card. Hands off to Dana. |
| `/sdd-config [show\|init\|validate\|sources]` | Inspect or initialize the layered config — global, project, env vars. See `CONFIG.md`. |

### MCP server

The plugin registers an MCP server called `sdd-governance` that exposes governance as native Claude tools, scoped to whichever repo Claude Code has open (via `${CLAUDE_PROJECT_DIR}`). Tools available:

- `list_capabilities`, `get_capability`
- `list_tasks`, `get_task`
- `get_acceptance`
- `list_findings`, `search_findings`, `get_finding`
- `validate`

You don't have to invoke these directly — Claude will reach for them when relevant. They're how the AI gets the framework into its tool palette instead of just reading docs.

## Configuration

The plugin works with zero config — every option has a sensible default. Two things make the config layer worth setting up:

1. **A shared findings wiki.** Per-repo findings are invisible outside that repo. Pointing `wiki.repo` at a shared git repo (e.g. `https://github.com/mansura-habiba/altaria-llm-wiki`) turns findings into an org-wide knowledge layer that Bob reads before scaffolding and Dana publishes to after review.
2. **Sensible team defaults.** Tier (`solo` vs `team`), AI-resistance policy, validation strictness, MCP transport.

Bootstrap a global config (applies to every repo you work in):

```bash
mkdir -p ~/.config/sdd
cp examples/sdd-config.example.yaml ~/.config/sdd/config.yaml
$EDITOR ~/.config/sdd/config.yaml
```

Or a project-level config (overrides global for this repo only):

```bash
cp examples/sdd-config.example.yaml .governance/config.yaml
```

The plugin's MCP server inherits a curated set of `SDD_*` env vars from your shell, so you can temporarily override config without editing files:

```bash
export SDD_WIKI_REPO=https://github.com/mansura-habiba/altaria-llm-wiki
export SDD_WIKI_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
# now /sdd-config show, @bob-scaffolder, @dana-reviewer all see the wiki
```

Precedence (later wins): built-in defaults → `~/.config/sdd/config.yaml` → `.governance/config.yaml` → `SDD_*` env vars.

Full documentation: [`CONFIG.md`](./CONFIG.md). Schema: [`.governance/sdd-config.schema.yaml`](./.governance/sdd-config.schema.yaml). Worked example: [`examples/sdd-config.example.yaml`](./examples/sdd-config.example.yaml).

## Typical workflow

1. `/sdd-init` — bootstrap the framework if the repo doesn't have one
2. `@bob-scaffolder` — "scaffold a capability for parsing config files"
3. (You or another mode implement against the scaffolded acceptance)
4. `/sdd-finding-add` — record any judgment calls that came up
5. `/sdd-review <task-id>` — Dana reviews against the contracts
6. `/sdd-validate` — final check before merge

## Updating

When this repo publishes a new plugin version, refresh from inside Claude Code:

```text
/plugin marketplace update sdd-plus-plus-marketplace
/plugin update sdd-plus-plus
```

## Uninstalling

```text
/plugin uninstall sdd-plus-plus
/plugin marketplace remove sdd-plus-plus-marketplace
```

The Python package (`pip install sdd-plus-plus`) is separate — uninstall it with `pip uninstall sdd-plus-plus` if you no longer want the CLI either.

## Troubleshooting

**`sdd-governance` MCP server fails to start.** The `sdd` binary isn't on `$PATH`. Run `which sdd` outside Claude Code; if empty, `pip install 'sdd-plus-plus[serve]'` and restart Claude Code.

**`/plugin marketplace add` says the marketplace can't be found.** Confirm `.claude-plugin/marketplace.json` is on the default branch of the repo you're pointing at. Marketplaces are discovered from the default branch, not the current working copy.

**Agents don't appear after install.** Run `/plugin list` to confirm the plugin is enabled. If it is, restart Claude Code — agent registration happens at session start.

**MCP tools call `sdd` but get "no .governance/ in this repo".** The MCP server uses `${CLAUDE_PROJECT_DIR}` as its `--target`. Make sure Claude Code is opened in the repo you actually want governance to operate on, not the plugin's own repo.
