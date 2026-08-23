# philosophy.md — Read this first, and re-read it if you're about to improvise

## The one sentence

> **We are not replacing the `if`. We are discovering which `if` should exist.**

If a change you're about to make doesn't serve that sentence, stop and flag it instead of building it.

## What the demo has to prove — nothing more, nothing less

> A system discovers a useful policy that nobody explicitly programmed, explains it,
> gets human approval, and enforces it on a new, unseen case.

This is the entire north star for the prototype. Not an enterprise governance platform.
Not a dashboard. Not a collection of detectors. One closed loop, proven with real numbers
from real code, end to end.

## The loop (do not rename, reorder, or collapse these steps)

```
Observe → Discover → Propose → Approve → Enforce → Observe again
```

- **Observe**: historical AI decisions, human overrides, and business outcomes are data,
  already collected (see `insurance_claims.csv`).
- **Discover**: a statistical/interpretable rule-mining process finds a candidate policy
  in that data. This step must never be hardcoded or scripted to "find" a
  predetermined answer — see `conventions.md` for what disqualifies a result.
- **Propose**: the candidate becomes a human-readable diff plus a rationale. An LLM may
  draft the rationale text. An LLM may never decide the conditions.
- **Approve**: a human clicks Approve / Edit / Reject. This gate is not optional and not
  simulated — it must be a real state transition in the code.
- **Enforce**: the approved policy is compiled into deterministic, versioned JSON and
  evaluated by ordinary code (if/else, not a model) at runtime.
- **Observe again**: the loop starts over on new data.

## The governing engineering principle (this is the actual product)

> **AI does discovery and drafting. Deterministic systems do enforcement.**
> No generative model is ever the final authority over a consequential action.

Concretely: an LLM may write the sentence explaining *why* a policy is being proposed.
An LLM must never be the thing that returns `AUTO_PROCESS` or `HUMAN_REVIEW` for a live
claim. That decision is always a deterministic evaluation against a versioned policy
object. If you ever find yourself piping a claim through an LLM to get a routing
decision, you have broken the architecture — stop and flag it.

## Why this framing exists (context, not busywork)

The project spent two rounds of adversarial narrowing rejecting: a generic AI checker,
a behavioral firewall, a dynamic permission governor, and a message-recall system —
each demoted or rejected because it was either commodity (already exists as a product
category) or didn't survive "if you remove the AI, does the demo still work as five
lines of code?" The surviving idea is **policy discovery from evidence**, specifically
because removing the AI *does* break it — pattern discovery genuinely requires it,
enforcement genuinely doesn't. Preserve that asymmetry. It is the whole pitch.

## Frozen — do not change without a strong, explicitly stated reason

- The Observe → Discover → Propose → Approve → Enforce loop, in this order.
- The AI-does-discovery / deterministic-does-enforcement boundary.
- The human-approval gate as a mandatory, non-bypassable step.
- Insurance claims as the demonstration domain for the MVP.
- Performance / cost / responsibility as the reporting dimensions (even though the
  detection layer underneath may use finer-grained multi-label signals — see
  `architecture.md`).

## Still open — safe to iterate on, no permission needed

- Exact API routes, DB schema, frontend framework, file layout details (as long as they
  match `architecture.md`'s component boundaries).
- Specific rule-mining implementation details, as long as it stays interpretable
  (see `conventions.md`).
- Exact wording of the LLM-generated rationale text.
- Frontend visual design.

## Do not reopen without new evidence — already attacked and rejected

- A generic "AI safety checker" or "AI firewall" framing.
- Message recall (editing a response after a side effect has already happened) — this
  is logically incoherent, not just deprioritized. Do not build it.
- PII filtering, token caps, or generic model routing presented as *the* differentiator
  (they're fine as supporting features, never as the pitch).
- A broad "AI governance dashboard" as the product framing.
- Letting an LLM directly modify the live policy without the human-approval gate.

## When you're unsure

Prefer the smaller, more literal interpretation of a task over the more impressive one.
An MVP that does the six-step loop honestly, on real (if small) numbers, beats a bigger
system that fakes or skips a step. If a task in `tasks.md` seems to require inventing a
new component not described in `architecture.md`, stop and ask rather than improvising —
see the "Stop and ask" section in `tasks.md`.
