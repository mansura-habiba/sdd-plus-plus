---
description: Inspect, initialize, or validate the active sdd-plus-plus config — including the wiki repo and other layered settings.
argument-hint: "[show|init|validate|sources] [--global|--project]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

Handle config operations for sdd-plus-plus. The active subcommand is in `$ARGUMENTS`.

## Subcommands

### `show` (default if no subcommand given)
Print the effective merged config — what sdd actually sees after applying defaults → global → project → env vars.

1. Read built-in defaults from `.governance/sdd-config.schema.yaml` (the `default:` values).
2. Layer on `~/.config/sdd/config.yaml` if it exists.
3. Layer on `.governance/config.yaml` if it exists.
4. Layer on any `SDD_*` env vars present.
5. Print the merged YAML.
6. If `wiki.repo` is unset, flag it: *"No wiki repo configured. Findings will be local-only. See CONFIG.md to wire one up."*

### `init [--global|--project]`
Create a starter config file from `examples/sdd-config.example.yaml`.

- `--global` writes to `~/.config/sdd/config.yaml` (default if neither flag is passed).
- `--project` writes to `.governance/config.yaml`.

Refuse to overwrite an existing file. Surface the path and tell the user to edit it.

### `validate`
Validate every config file in the precedence chain against `.governance/sdd-config.schema.yaml`. Report:

- Each file checked and pass/fail.
- For failures, the specific schema field and the actual value.
- A warning if `auto-sync` + `any-author` are both set (dangerous combination — see CONFIG.md).
- A warning if `wiki.auth.method: https-token` is set but the env var named in `token_env_var` is empty in the current shell.

### `sources`
For each key in the merged config, report which source supplied the value: `default`, `global`, `project`, or `env`. Useful for "why is this set to X" questions.

## Default behavior

If `$ARGUMENTS` is empty, run `show`.

## Hand-off

If validation surfaces wiki-related errors that suggest the wiki layer needs setup, offer to walk through it. If the config file doesn't exist yet, offer to run `init` automatically.

Do not edit any file other than the config files this command manages.
