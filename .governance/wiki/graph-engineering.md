# Graph engineering playbook

> Task: [GRAPHIFY-2](tasks/GRAPHIFY-2.md) · Design: [graphify-x-llm-wiki.md](graphify-x-llm-wiki.md)  
> Audience: developers and AI assistants using `sdd graph` / MCP `kb_*`

## What this is

**Graph engineering** = build and query a durable knowledge graph so agents stop
relying on chat transcripts. SDD findings remain authoritative for lifecycle
(`suspected` → `confirmed`). Graphify is retrieval + shared memory.

**What this is not:** a multi-agent runtime. Roles below are *how humans and AI
sessions cooperate*, all reading the same graph.

## The ladder → concrete tools

| Step | Practice | Developer | AI (MCP) |
|---|---|---|---|
| 1 Reflection | Challenge before complying; learn from past Q&A | `sdd graph reflect` | `kb_reflect` |
| 2 Tool use | Search the graph / findings — don't invent structure | `sdd graph query/path/explain` | `kb_query` / `kb_path` / `kb_explain` |
| 3 Planning | Break work into a draft plan citing graph hits | `sdd plan new` | `propose_plan` |
| 4 Multi-agent | Separate code / review / test *sessions* sharing the graph | same graph path | same `kb_*` |
| 5 Critique | One critique pass after every generation | Cursor `/sdd-graph` | re-run `kb_query` + challenge |
| 6 Shared memory | Persist useful answers; chat forgets, graph doesn't | `sdd graph memory save` | `kb_memory_save` |

## Session loop

```text
1. Challenge the ask (AGENTS.md §1)
2. kb_query / sdd graph query  — what already connects?
3. search_findings / get_finding — authoritative gotchas
4. propose_plan with challenge citing graph + findings
5. Human accepts plan
6. Implement
7. Critique once (diff vs plan + re-query neighbors)
8. kb_memory_save useful results; periodically kb_reflect
9. sdd graph update  (after meaningful code changes)
```

## Install (once per machine)

```bash
pipx install graphifyy          # CLI name is still `graphify`
graphify cursor install         # optional Cursor rule
sdd graph status                # should show graphify + graph.json
sdd graph update                # AST refresh, no API key
```

Optional config (`.governance/config.yaml`):

```yaml
knowledge:
  graphify:
    enabled: true
    graph_path: graphify-out/graph.json
```

## Authority boundary

| Need | Tool |
|---|---|
| Finding by id / status / tag | `get_finding` / `list_findings` |
| Substring over findings | `search_findings` |
| “What connects X to Y?” | `kb_path` / `sdd graph path` |
| Architecture / cross-cutting | `kb_query` / `sdd graph query` |
| Persist session learning | `kb_memory_save` / `sdd graph memory save` |

Never treat Graphify INFERRED edges as confirmed findings.
