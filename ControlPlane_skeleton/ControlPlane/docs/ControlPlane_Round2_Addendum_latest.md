# ControlPlane.ai — Round 2 Addendum: Responding to the Expanded Brief

**Appended to the Round 1 research paper. Does not replace it — extends Sections 4–6 and 10 with mechanisms specific to the Round 2 prompt.**

---

## A. Why this is an addendum, not a rewrite

Round 2 broadened the brief (multiple simultaneous use cases, overlapping risk categories, no reliable ground truth, over/under-flagging tradeoffs, multi-turn/agentic risk, evolving regulation, API-only model access, latency at scale) but did **not** invalidate anything frozen in Section 10 of the Round 1 paper. The Observe → Discover → Propose → Approve → Enforce loop, the AI/deterministic boundary, and insurance claims as the proving domain all remain load-bearing. What the expanded brief requires is that three components inside that architecture — which were previously described in outline — now need an explicit mechanism, because the prototype has to demonstrate them, not just describe them.

The mapping from brief to existing architecture:

| Accenture concern | Where it already lives in the frozen architecture | What's new in this addendum |
|---|---|---|
| Different use cases, different risk/latency tolerance | Deterministic fast path (§6.4) | Use Case Profiles (§B below) |
| Bias/hallucination/privacy overlap | Detection layer (§6.2, "fuzzy risk scoring") | Multi-label risk vectors (§C below) |
| No reliable real-time ground truth | Evidence grounding (§6.2) | Verifiable vs. unverifiable claim routing (§D below) |
| Over/under-flagging tradeoff | Intervention taxonomy (§6.5) | Now explicitly configurable per Use Case Profile — see §B |
| Multi-turn / agentic compounding risk | Consequence-control thesis (§3.2, rejection of Idea H) | Already covered: policy sits at the execution/action boundary, not the message boundary. No new mechanism needed — flagged here so it isn't mistaken for a gap. |
| Evolving regulation | Policy versioning (§6.7) | Already covered: a regulatory change is just a new policy proposal source (human-authored this time, not discovered) feeding the same approve → version → deploy pipeline. |
| API-only model access | System overview (§5.1, "model-agnostic") | Already covered: the architecture never inspects model internals; no new mechanism needed. |
| Latency at scale (tens of thousands/week) | Latency strategy (§6.4) | Confirmed at the new volume — see §B, since profile-specific thresholds are what actually keep the fast path fast under mixed load. |

Three of the eight brief items require genuinely new mechanism (B, C, D below). The remaining five are already answered by the frozen architecture and are listed here so the team doesn't waste time re-solving them.

---

## B. Use Case Profiles (answers: different risk tolerance, latency budgets, over/under-flagging tuning)

**Problem:** the Round 1 architecture describes one organization running one evolving policy. The Round 2 brief assumes one organization running several AI systems at once — a customer chatbot, an internal copilot, a decision-support tool — each with a different acceptable latency and a different acceptable false-positive/false-negative balance. A single global threshold is wrong for all three simultaneously: the chatbot needs sub-second answers and can tolerate more false positives (a slightly-too-cautious deflection is cheap), the decision-support tool can tolerate seconds of latency but a false negative is expensive.

**Mechanism:** insert a **Use Case Profile** layer between the org-level policy and the deterministic runtime evaluator. The discovery engine, evidence pipeline, and policy schema stay shared — this is what keeps the system one product, not three. What varies per profile:

```
ORG-LEVEL POLICY
(shared: what counts as a violation category, trusted data sources,
 audit requirements)
        │
   ┌────┼─────────────────┐
   ▼    ▼                 ▼
Customer Chatbot   Internal Copilot   Decision-Support Tool
─────────────────  ─────────────────  ─────────────────────
latency budget:     latency budget:    latency budget:
 <300ms              <2s                <30s (human is already
                                          in the loop)
default posture:     default posture:   default posture:
 favor ALLOW/MODIFY   favor VERIFY       favor ESCALATE
 (deflect false        (ask, don't       (stakes justify
 positives cheaply)     silently pass)    slower, stricter path)
evidence pool:        evidence pool:     evidence pool:
 chatbot transcripts   copilot sessions   claim/decision records
 (own discovery run)   (own discovery     (own discovery run)
                        run)
```

Each profile is evaluated by the same deterministic engine against its own current policy version. Discovery can be run **per profile** (a pattern found in decision-support data should not silently govern the chatbot) or **cross-profile** when a signal genuinely generalizes (e.g., a specific PII leakage pattern) — but cross-profile promotion of a discovered rule requires the same human-approval gate as any other policy change, applied by someone with authority over both profiles. This prevents one workflow's noisy data from quietly reshaping another's behavior.

This also directly answers the over-flagging/under-flagging tradeoff item: the tradeoff isn't solved algorithmically, it's made an explicit, visible, per-profile policy parameter that a human sets and can see the consequences of — which is honestly a stronger answer than claiming to have optimized it away.

**Prototype scope note:** the full prototype does not need three live systems. It needs the profile abstraction to exist in the policy schema and the demo needs to show *one* profile's evidence-discovery-approval loop end to end, with a second profile shown only as "same engine, different thresholds" — enough to prove the abstraction without tripling the build.

---

## C. Multi-label risk vectors (answers: bias/hallucination/privacy overlap)

**Problem:** the Round 1 detection layer implicitly treated performance/cost/responsibility risk as separable categories with independent scores. The Round 2 brief correctly points out that a single flagged span is often several things at once — a fabricated detail about a real person is simultaneously a hallucination and a privacy concern, and the combination is more dangerous than either alone.

**Mechanism:** a flagged span carries a **risk vector**, not a single score:

```
FLAGGED SPAN: "John Doe's diagnosis is [fabricated condition]"

risk_vector: { hallucination: 0.81, privacy: 0.94, bias: 0.12 }
```

Policy conditions can reference label *combinations*, not just individual thresholds — this reuses the exact multivariate condition-matching machinery already specified for business-context policy discovery in §6.7 (e.g. "premium tier + airline fault + verified docs"). The same mechanism that discovers `customer_tier == premium AND incident_type == airline_fault` can discover `hallucination > 0.6 AND privacy > 0.6 → escalate as PRIVACY_CRITICAL, not generic hallucination`. No new discovery algorithm is required — just applying the existing one to risk-label co-occurrence as an additional feature space, alongside business context.

This keeps performance/cost/responsibility as the org-facing reporting dimensions (nothing in §10's frozen list is violated), while the underlying detection layer is honest about the fact that real flagged content rarely sorts cleanly into one bucket.

---

## D. Verifiable vs. unverifiable claims (answers: no reliable real-time ground truth)

**Problem:** §6.2 of the Round 1 paper described evidence grounding as "bounded LLM comparison against retrieved facts," which implicitly assumes a retrievable fact exists. The Round 2 brief is explicit that it often doesn't — open-ended claims, predictions, and novel situations have no source document to check against, and this is the same knowledge gap that produces the hallucination in the first place.

**Mechanism — and this is a reframe of the pitch, not a patch:** split claim handling into two lanes at generation time.

```
CLAIM
  │
  ├── Verifiable now (a retrievable fact exists)
  │      → bounded evidence-grounding check (existing §6.2 mechanism,
  │        unchanged)
  │
  └── Not verifiable now (opinion, prediction, novel combination,
      no source document)
         → cannot be checked for correctness at generation time
         → tagged UNVERIFIED, routed by *downstream consequence*
           (what does this claim let the AI or user do next?),
           not by a correctness judgment nobody can make yet
         → once an outcome eventually materializes (dispute,
           confirmation, reversal, complaint), it becomes training
           signal for the discovery engine: was this kind of
           unverifiable claim, in this kind of context, usually
           fine or usually costly?
```

The honest claim for the pitch, and it should be stated this bluntly to a judge: **we do not claim to solve real-time verification of unverifiable claims — nobody can, and any team that claims otherwise is overselling.** What ControlPlane claims is that when ground truth is unavailable at generation time, routing by downstream consequence and later validating against actual outcomes is a more defensible answer than pretending a checker can verify the unverifiable. This is not a new component — it is exactly the outcome-aware policy discovery loop from §6.6, applied to the specific case where evidence grounding has nothing to check against. It should be framed in the pitch as the paper's central idea proving its worth on the brief's hardest stated problem, not as a bolted-on fix.

---

## E. Updates to Section 10 (Frozen / Open / Do-not-reopen)

Add to **Frozen**: Use Case Profiles as the mechanism for per-workflow risk/latency variation; multi-label risk vectors as the mechanism for overlapping risk categories; the verifiable/unverifiable claim split as the mechanism for absent ground truth. All three are extensions of already-frozen mechanisms (multivariate policy conditions, outcome-aware discovery), not new architectural commitments — reopening the underlying loop or the AI/deterministic boundary is still out of scope without strong new evidence.

Add to **Still open**: which single Use Case Profile the prototype demonstrates live vs. references only; the specific feature representation used for risk-label co-occurrence; whether the unverifiable-claim lane is demoed at all in the Round 2 prototype or only described in the README (build-time call, not an architecture call).

No changes to **Do not reopen**.

---

## F. What this means for build order (confirms, does not replace, the senior's four-step plan)

This addendum changes zero lines of build-priority logic — the discovery engine on the insurance domain is still step one, exactly as already agreed. What it does is make sure that when the discovery engine and policy lifecycle are built, the **policy schema itself** is built wide enough from the start to carry a use-case profile field and a risk-vector field, so retrofitting isn't needed later. That's a data-modeling decision to make in step 1–2 of the build (dataset schema, policy representation), not a new phase.
