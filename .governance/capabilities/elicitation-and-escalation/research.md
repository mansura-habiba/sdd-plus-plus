# Research analysis — elicitation and escalation for coding assistants

> **The question this research answers.** Coding assistants today default to two failure modes: either they proceed confidently on a 60% guess, or they ask five trivial questions that don't change the outcome. The framework already has scaffolding for challenge-before-comply (instructions.md §1, §9, §12). What's missing is the executable contract that turns those rules into refusable artifacts. This document grounds the design in cross-industry handoff protocols.

The closest published prior art lives outside software engineering. Aviation, healthcare, and manufacturing have spent decades refining how a system signals uncertainty and demands human attention. Software engineering is the laggard. Each of these industries solved a version of the problem coding assistants face today; the patterns transfer.

---

## 1. What the framework already has — and what's missing

The grounding documents are unambiguous about the intent. `instructions.md §1` forbids sycophancy and requires a four-step challenge (restate, concerns, alternatives, plan). `§9` explicitly lists uncertainty triggers and instructs the AI to ask. `§12` formalizes confidence calibration with a 0–1 scale and mechanical autonomy downgrade for persistently overconfident agents. The plan schema enforces a `challenge` block as a structural requirement — empty challenge means invalid plan.

That foundation is unusually mature. Most teams trying to "make AI ask more questions" don't have any of this; they're starting from "be careful out there" in a prompt.

The gaps, surfaced honestly:

**No `status: blocked` in the plan lifecycle.** The current statuses are `draft → accepted → executed → archived → rejected`. There's no formal state for "the AI started, hit a wall, and explicitly stopped pending human input." Without it, the AI's only options when blocked are to fabricate a plan it doesn't believe in (failure mode), or to chat the human and hope it gets back to a coherent state (no audit trail).

**No per-capability elicitation triggers in the spec.** The §9 triggers in instructions.md are generic ("if a non-goal is ambiguous, ask"). But "ambiguity" varies by capability. A payments capability needs the AI to escalate on currency handling; a UI capability needs it to escalate on a11y interpretation; a security capability needs it to escalate on threat-model assumptions. The capability spec is the natural place to declare "for this capability, these specific situations require elicitation or escalation" — but the schema doesn't have a field for it yet.

**No dedicated elicitation agent.** Bob scaffolds; Dana reviews. Both already do some asking, but the asking is interleaved with their other work and competes with it. When Bob is mid-scaffold, "ask more questions" runs against "produce the bundle". A separate role — elicitation-only — sidesteps the conflict.

**No validation rule against unreferenced escalations.** The framework's discipline against orphan acceptance assertions (every assertion must have a `case_id`) doesn't extend to escalations. An AI can write "I'm escalating because this is uncertain" and that escalation has no anchor — no `case_id`, no `forbidden` item, no finding reference. Unanchored escalations are theater.

These four gaps are the surface area of this capability. Everything below grounds the design.

---

## 2. Aviation — positive control and the "I have control / you have control" protocol

Commercial aviation eliminated a class of accidents in the 1990s by enforcing **positive transfer of control**. When the captain hands flying to the first officer, both pilots speak: *"I have control" — "You have control" — "I have control."* The exchange is verbal, explicit, and non-overlapping. The aircraft is never *maybe* being flown by one or the other. The protocol exists because ambiguous handoffs killed people.

The transferable lesson for coding assistants: every handoff must be explicit, must have a verbal (or structural) confirmation, and must leave no ambiguity about who is responsible for the next step. A coding assistant that drifts into "I'll just take a look and maybe make some edits" without explicit positive control is in the same failure mode as a flight deck where neither pilot is sure who's flying.

In sdd-plus-plus terms: when the AI hits `status: blocked`, the handoff to the human must be unambiguous. The plan moves to `blocked`; the `block_reason` is structured; the human's next action is named. No "I think you should look at this" — *"I have stopped. You have control. Here is what to resolve before I can continue."* Symmetrically, when the human responds and the AI resumes, the AI moves the plan back to `draft` with a recorded acknowledgment of the resolution.

Aviation also formalized the **CRM (Crew Resource Management)** doctrine: subordinate crew members are required to challenge the captain when they see a safety risk, and captains are required to *accept the challenge as valuable* rather than override. The instructions.md §1 sycophancy prohibition is the same idea applied to AI — the AI is required to challenge, the human is required to receive the challenge as input rather than dismiss it. Worth strengthening: the framework can make this *measurable* by counting challenges raised vs accepted vs rejected, and flagging plans whose challenge blocks are visibly perfunctory.

---

## 3. Manufacturing — the andon cord and stop-the-line authority

The Toyota Production System gave every worker on the line the authority to **stop the entire line** by pulling an overhead cord (the andon cord). The cord wasn't reserved for senior workers; a brand-new operator could stop a billion-dollar production line if they saw a defect. The reason: defects compound. Letting a flaw move down the line is exponentially more expensive than stopping at the source.

Healthcare adopted this directly — the "stop the line" protocol now appears in surgical safety checklists (WHO Surgical Safety Checklist, 2009) and ICU rounds. Any team member, including the most junior, can halt the procedure if they observe something wrong. The protocol's design includes a critical detail: **the stop must be heard, not interpreted.** Saying "I'm uncomfortable with this" is not a stop. Saying "I am stopping the procedure pending clarification on X" is.

For coding assistants: the equivalent is a formal stop primitive that is **heard, not interpreted**. A coding assistant that says "I'm not sure, but I'll try" is in the failure mode the andon cord was invented to prevent. The framework needs `status: blocked` with a structured `block_reason` that names *why* and *what unblocks*. Vague reasons must fail validation. The AI's stop must be as audible as a pulled cord.

A related Toyota practice: the andon cord triggers a **time-bounded resolution**. The line restarts within a small window or the defect is escalated up the management chain. The coding-assistant analogue is a stale-block timeout — if a plan sits in `status: blocked` for N days without human resolution, `sdd doctor` flags it. This makes blocking lossy unless someone owns the unblock; quiet permanent blocks become visible.

---

## 4. Healthcare — SBAR and structured handoff

Communication failures in clinical handoffs were a leading cause of preventable medical errors before SBAR was formalized in the early 2000s. SBAR forces every handoff to follow a four-part structure:

- **Situation** — what is happening right now
- **Background** — relevant history and context
- **Assessment** — what I think is going on
- **Recommendation** — what I think should happen next

The structure is enforceable, teachable, and grading-able. Hospitals that adopted SBAR saw measurable reductions in handoff-related adverse events (multiple studies cited in the AHRQ TeamSTEPPS curriculum).

The transferable insight is that **structured handoffs reduce error precisely because they're enforceable**. A handoff template that requires the deliverer to articulate Situation + Background + Assessment + Recommendation cannot be silently skipped — the absence is visible.

For coding assistants escalating to humans, the SBAR shape maps cleanly: when an AI fills in `block_reason`, the schema should require four fields:

- **what_i_was_doing** — the task the AI was working on
- **what_made_me_stop** — the specific ambiguity, conflict, or risk that triggered the stop
- **what_i_think** — the AI's best assessment of the resolution paths
- **what_i_need_from_you** — a specific request: a decision between A and B, a confirmation of policy, an unblocking input

A `block_reason` without one of these is a hesitation, not an escalation. The schema should refuse it.

---

## 5. The question-quality literature — what makes a good clarifying question

Less well-known but directly relevant: there's an emerging literature on *clarifying questions for code understanding*, primarily from the conversational-AI community. The TREC Conversational Assistance Track (CAsT) and related work on clarifying question generation (e.g. Aliannejadi et al., SIGIR 2019; Zamani et al., 2020) converge on a few patterns:

1. **Specificity beats coverage.** One precisely-scoped question that resolves a binary ambiguity is more valuable than five generic questions that don't.
2. **Show the default action.** A good clarifying question includes "if you don't answer, here's what I'll do" — making the cost of silence visible.
3. **Cite the source of the confusion.** "Acceptance case `auth-rejects-empty-token` is unclear about token format — is an empty string the same as a missing token?" beats "I have a question about authentication."
4. **Bound the question count.** Beyond three questions per turn, the marginal value collapses and the human disengages.

The transferable design: a "question quality" rule that any elicitation produces *cited, specific, bounded* questions, each with a stated default action. Eve the Elicitor's instructions encode exactly this.

---

## 6. The calibration problem — why self-reported confidence isn't enough

The framework's §12 confidence calibration is a strong move, but the published literature on AI self-confidence is unflattering. Large language models are systematically overconfident on facts they should be uncertain about, and underconfident on facts they should be sure about (Lin et al., "Teaching Models to Express Their Uncertainty in Words," 2022; Tian et al., "Just Ask for Calibration," EMNLP 2023). The calibration error is large enough that raw self-reported confidence is roughly as useful as no signal at all.

What works better, per the same literature:

- **Multi-perspective ask** — ask the same question in three different framings and check whether the answer is consistent. Inconsistency is a stronger signal of uncertainty than the AI's reported confidence.
- **Verifier model** — a separate model (or the same model with adversarial framing) audits the proposed plan and surfaces disagreement.
- **Counter-example generation** — the AI is required to produce one scenario where its plan fails. If it can't, the plan is suspect.

The §12 calibration mechanic — *over time, the framework tracks whether 90% predictions hit 90%* — is the right long-term answer. Mechanical calibration based on outcomes beats reported confidence by a wide margin. The short-term gap is *between* sessions, before calibration data accumulates. For that gap, the framework can ship the multi-perspective ask as a question-quality rule: any elicitation that resolves a high-stakes ambiguity must be cross-checked by reframing.

---

## 7. The dedicated-role argument — why Eve, not "Bob asks more"

A reasonable objection: instructions.md §1 already requires Bob to challenge. Adding Eve seems like duplication. The argument for a dedicated role:

When one agent does both scaffolding and elicitation, the scaffolding work creates pressure to truncate the elicitation. Studies of clinical handoffs show this directly: the same physician handling both diagnosis and treatment skips diagnostic questions to get to the treatment they're already planning. Separation of concerns at the *role* level — diagnostician hands off to surgeon — produces better diagnostic completeness.

Coding assistants exhibit the same pressure. The model trained on "produce a useful artifact" pulls toward producing; the same model asked to "challenge first" produces a perfunctory challenge if it's already drafting the scaffold in its head. A separate Eve role — whose entire job is elicitation, with no scaffolding output — sidesteps the pull.

This is also why aviation has separate roles for pilot flying vs pilot monitoring on every commercial flight, even when the same person could in principle do both. The separation is the safety mechanism.

---

## 8. The single-page summary

| Mechanism | Maps onto | Why it works |
|---|---|---|
| Trigger taxonomy in capability spec | Aviation crew-resource-management challenge protocol | Makes "when to ask" enforceable per-capability, not generic |
| `status: blocked` with structured reason | Toyota andon cord, SBAR handoff | Stop must be heard, not interpreted; structure prevents theater |
| Question quality rules | TREC CAsT clarifying-question literature | Specificity + default action + citation + bounded count |
| Confidence calibration (already exists) + multi-perspective ask | Lin et al., Tian et al. on LLM calibration | Self-reported confidence is noise; multi-frame ask is signal |
| Eve the Elicitor as a dedicated agent | Clinical role separation, aviation pilot-flying/monitoring split | Removes the pull from "I'm already scaffolding" → truncated challenge |
| Validation rule against unreferenced escalations | The framework's own discipline against orphan assertions | Anchored escalations are auditable; unanchored ones are theater |

---

## 9. What the design spec needs to do

Build on what's already there, do not duplicate it. Specifically:

- **Extend `capability_spec.schema.yaml`** with `elicitation_triggers:` and `escalation_triggers:` blocks. Both optional; both per-capability.
- **Extend `plan.schema.yaml`** with `status: blocked` as a new enum value and a `block_reason:` block that requires four SBAR-shaped fields.
- **Add Eve the Elicitor** as a third plugin agent with frontmatter and a prompt scoped strictly to elicitation.
- **Add a validation rule** in `sdd validate` that any `block_reason` references at least one `case_id`, `forbidden` item, or finding ID, and that the reference resolves.
- **Add a section to `instructions.md`** strengthening the existing §1 / §9 / §12 rules with the multi-perspective ask requirement for high-stakes elicitations.
- **Do not** invent new commands when existing ones extend cleanly. `sdd plan new --status blocked` is better than a new `sdd plan block` command.

The detailed how-to lives in `design.md`. The contract that must hold lives in `spec.yaml`. The why lives here.

---

## Sources

- **Aviation CRM**: NASA TM-2002-211393, *Crew Resource Management Training: A Practical and Conceptual Overview*.
- **Positive transfer of control**: FAA Advisory Circular 60-22, *Aeronautical Decision Making*.
- **Toyota Production System / andon cord**: Liker, *The Toyota Way* (2004); Spear & Bowen, "Decoding the DNA of the Toyota Production System," HBR 1999.
- **WHO Surgical Safety Checklist**: Haynes et al., *NEJM* 2009, 360:491–9.
- **SBAR in healthcare**: Haig et al., "SBAR: A Shared Mental Model for Improving Communication Between Clinicians," *Jt Comm J Qual Patient Saf* 2006.
- **TeamSTEPPS curriculum**: Agency for Healthcare Research and Quality (AHRQ).
- **Clarifying questions for IR**: Aliannejadi et al., "Asking Clarifying Questions in Open-Domain Information-Seeking Conversations," SIGIR 2019. Zamani et al., "Generating Clarifying Questions for Information Retrieval," WWW 2020.
- **LLM calibration**: Lin et al., "Teaching Models to Express Their Uncertainty in Words," TMLR 2022. Tian et al., "Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models," EMNLP 2023.
- **Sdd-plus-plus internal**: `.governance/instructions.md` §1, §9, §12; `src/sdd/_schemas/plan.schema.yaml`; `src/sdd/_schemas/capability_spec.schema.yaml`.
