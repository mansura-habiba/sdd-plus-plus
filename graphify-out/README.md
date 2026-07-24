# Graphify output

Built with [Graphify](https://github.com/Graphify-Labs/graphify).

| File | Purpose |
|---|---|
| `graph.json` | Queryable knowledge graph (committed; refresh with `make graphify-update`) |
| `manifest.json` | Extraction manifest |
| `cache/` | Local rebuild cache (gitignored) |

```bash
graphify query "<question>" --graph graphify-out/graph.json
graphify path "A" "B" --graph graphify-out/graph.json
graphify explain "concept" --graph graphify-out/graph.json
```

Code graph: `graphify update .` (no API key).  
Docs/wiki/PDF into the graph: `/graphify --update` or `graphify extract .` with an LLM backend.
