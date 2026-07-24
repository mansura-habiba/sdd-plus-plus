# Task: GRAPHIFY-1 — Add Graphify for knowledge-base search

> GitHub issue: https://github.ibm.com/MANSURAH/sdd-plus-plus/issues/5
> Project board: https://github.ibm.com/users/MANSURAH/projects/3 ("2026 project")

## Goal

Wire [Graphify](https://github.com/Graphify-Labs/graphify) into sdd-plus-plus so agents can search the repo knowledge graph for architecture and cross-cutting questions, without replacing SDD findings/MCP.

## Bigger picture

Substring `search_findings` only covers finding YAML. Graphify adds AST (and optional semantic) graph search over code + docs — useful for “what connects X to Y” before generating code.

## In scope (done this session)

- [x] `graphify cursor install` → `.cursor/rules/graphify.mdc` (customized to coexist with SDD MCP)
- [x] Initial code graph via `graphify update .` → `graphify-out/graph.json` (~994 nodes)
- [x] `.gitignore` for Graphify cache/html artifacts
- [x] Docs: README + `docs/how-to-use.md` Graphify section
- [x] `make graphify-update`
- [x] GitHub issue #5 on project "2026 project"

## Out of scope / follow-ups

- [ ] Human-authored capability `spec.yaml` for `graphify-kb-search` (registry requires `spec_path`; AI cannot author specs)
- [ ] Optional `sdd graph query` CLI / MCP wrappers around Graphify
- [ ] Semantic extract of `.governance/wiki`, `docs/`, whitepaper PDF into the graph (needs LLM backend)

## Challenge

- **Concern:** Stock Graphify Cursor rule mandates graphify before every Read/Grep — that fights AGENTS.md “use sdd MCP for findings.” Mitigated by rewriting the rule.
- **Concern:** Baking Graphify into the Python package as a hard dep is wrong — keep it optional/companion.
- **Alternative considered:** Only document Graphify externally. Rejected — dogfooding the graph in-repo is what makes KB search real for agents working here.
