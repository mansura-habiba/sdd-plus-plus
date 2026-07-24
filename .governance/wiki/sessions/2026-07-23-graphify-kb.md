# Session: 2026-07-23 — Graphify KB search dogfood

## Summary

Added Graphify as the companion knowledge-graph search layer for this repo.

## What landed

- `.cursor/rules/graphify.mdc` — agents use `graphify query|path|explain` for architecture; SDD MCP remains source of truth for findings/specs/plans
- `graphify-out/graph.json` — AST graph from `graphify update .` (~994 nodes / ~1661 edges)
- Docs in `README.md` and `docs/how-to-use.md`; `make graphify-update`
- Roadmap capability stub `graphify-kb-search` in `REGISTRY.yaml`
- Local task: `.governance/wiki/tasks/GRAPHIFY-1.md`

## Blockers

- Semantic indexing of wiki/docs/PDF needs an LLM backend (`graphify extract` / `/graphify --update`)
- Capability registry entry deferred: `spec_path` is required and specs are human-authored

## Next

1. Human author `capabilities/graphify-kb-search/spec.yaml` if promoting beyond dogfood
2. Optional: MCP/CLI wrappers once the spec exists and a plan is accepted
3. Track on https://github.ibm.com/MANSURAH/sdd-plus-plus/issues/5
