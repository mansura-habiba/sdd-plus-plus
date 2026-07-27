# Task: GRAPHIFY-2 — Graph engineering CLI + MCP tools

> GitHub issue: https://github.ibm.com/MANSURAH/sdd-plus-plus/issues/8
> Project board: https://github.ibm.com/users/MANSURAH/projects/3 ("2026 project")
>   — item-add blocked until `gh auth refresh -h github.ibm.com -s read:project,project`
>
> Extends: [GRAPHIFY-1](./GRAPHIFY-1.md), design note
> [graphify-x-llm-wiki.md](../graphify-x-llm-wiki.md)

## Goal

Give developers and AI users optional Graphify-backed tools (`sdd graph …` + MCP
`kb_*`) so they can practice **graph engineering** — query, path, explain, update,
and shared memory — without replacing SDD findings authority or building an agent runtime.

## Bigger picture

GRAPHIFY-1 dogfooded the code graph and Cursor rule. GRAPHIFY-2 makes that surface
reachable through the same `sdd` CLI / MCP path agents already use for plans and
findings. The reflection → tools → planning → multi-agent ladder is a **playbook**
mapped onto these tools, not a new orchestrator inside sdd.

## Challenge

- **Understood request:** Ship CLI + MCP wrappers so any developer or AI can engineer
  with the repo knowledge graph and persist memory across sessions.
- **Concern:** Shipping tools without a human capability `spec.yaml` repeats
  `framework-capabilities-undocumented`. Mitigation: task + playbook first; human
  authors `graph-engineering/spec.yaml` + registry entry before promoting active.
- **Concern:** Hard-depending Graphify in the package is wrong. Prefer subprocess
  wrappers that degrade with install hints when `graphify` / `graph.json` is missing.
- **Alternative rejected:** Multi-agent LLM runtime inside sdd — wrong product boundary.
- **Alternative rejected:** Docs-only — developers and MCP clients need a first-class
  `sdd graph` / `kb_*` surface.

## In scope

- [x] Task card GRAPHIFY-2
- [x] GitHub issue #8 (https://github.ibm.com/MANSURAH/sdd-plus-plus/issues/8)
- [ ] Project board item (needs `gh auth refresh -h github.ibm.com -s read:project,project`)
- [x] `src/sdd/commands/_graphify.py` helper (optional subprocess)
- [x] `sdd graph status|update|query|path|explain|memory|reflect`
- [x] MCP `kb_query` / `kb_path` / `kb_explain` / `kb_memory_save` / `kb_reflect`
- [x] Playbook + Cursor command + docs
- [x] Unit tests for missing-graphify fallback
- [ ] Human-authored capability `spec.yaml` + REGISTRY roadmap entry (human only)

## Out of scope / non-goals

- Multi-agent execution engine or tool/API runner
- Replacing `search_findings` / finding lifecycle with Graphify edges
- Hard dependency on the `graphify` Python package
- AI-authored capability contract

## Draft plan (awaiting human capability + `sdd plan accept`)

Formal `.governance/plan/*.plan.yaml` is deferred until a human authors
`.governance/capabilities/graph-engineering/spec.yaml` (validate requires the
capability path). Execution proceeds under this task + the accepted Cursor plan
“Graph engineering tools.”

### Steps

1. Shared Graphify helper — resolve path, status, invoke CLI.
2. Wire `sdd graph` Click group.
3. Wire MCP `kb_*` tools with findings fallback for `kb_query`.
4. Config schema `knowledge.graphify` (enabled + graph_path).
5. Playbook, Cursor command, README / how-to-use.
6. Tests + `sdd validate` + progress / session note.

### Confidence

0.75 — wrapper path is clear from GRAPHIFY-1; human spec/acceptance remains the gate.
