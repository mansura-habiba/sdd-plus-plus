# Task: DOCS-1 — HTML guide for SDD++ SDLC

> GitHub issue: pending (create + add to project 3 once approved)
> Branch: `cursor/tech-debt-tracking` (or follow-up docs branch)

## Goal

Standalone HTML guide teaching how to use sdd-plus-plus across the software
development lifecycle — bootstrap through progress handoff.

## Challenge

- **Concern:** `whitepaper/sdd-plus-plus-overview.html` already explains the system;
  a second HTML that restates philosophy is noise. This page must be **operational**
  (stages, who acts, commands), not another manifesto.
- **Concern:** Inventing a lifecycle that contradicts `.governance/USAGE.md` would
  fork the contract. Guide must map 1:1 to USAGE + AGENTS flows.
- **Alternative:** Only extend USAGE.md. Rejected — user asked for HTML; a browser
  guide is easier for onboarding and demos.

## In scope

- [x] `docs/sdlc-guide.html` — lifecycle stages with CLI/MCP cues
- [x] Link from README
- [x] Local task + progress note
- [ ] GitHub issue + project board item (needs explicit approval / `gh issue create`)

## Out of scope

- Whitepaper rewrite
- New CLI / MCP tools
- Auto-generated from USAGE (hand-authored HTML is fine for v1)
