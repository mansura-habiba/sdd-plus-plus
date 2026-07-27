---
description: Run the graph-engineering loop — query the knowledge graph, critique once, save memory.
allowed-tools:
  - Bash
---

You are running the **graph engineering** playbook for this repo
(`.governance/wiki/graph-engineering.md`).

Follow this loop in order. Do not skip the critique step.

1. **Challenge** — Restate the user's ask, one concern, one alternative (AGENTS.md §1).
2. **Tool use** — Prefer graph tools before guessing structure:
   - `sdd graph status`
   - `sdd graph query "<question>"` (or MCP `kb_query`)
   - `sdd graph path "A" "B"` / `sdd graph explain "X"` when needed
   - For finding lifecycle (status/tags), use `sdd findings` / MCP `search_findings` — not Graphify alone.
3. **Plan** — If the work is non-trivial, draft or update a plan that cites graph hits + findings. Do not self-accept.
4. **Roles** — If the task spans code + review + test, treat them as separate passes sharing the same graph (not parallel LLM runtimes you invent).
5. **Critique** — After any generation, one self-review pass: does the diff match the plan? Re-query neighbors of touched symbols. Fix before claiming done.
6. **Memory** — For useful Q&A from this session:
   ```bash
   sdd graph memory save --question "..." --answer "..." --outcome useful
   ```
   Optionally `sdd graph reflect` to refresh lessons.

If `sdd graph status` reports graphify missing, print the install hint (`pipx install graphifyy`) and fall back to findings search — do not invent a graph.
