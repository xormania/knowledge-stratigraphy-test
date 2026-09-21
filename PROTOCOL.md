# Protocol

## Objective

Estimate a model route's **effective knowledge frontier** using dated, same-domain, closed-book probes.

This protocol is designed for comparisons such as:

- Claude Code route A vs route B;
- Claude Code vs Claude.ai;
- before vs after a suspected silent model swap;
- pinned model ID vs product alias;
- old client vs updated client when routing behavior may differ.

It does **not** establish backend identity. It measures behavioral evidence consistent with different latent knowledge.

## 1. Isolation

For every trial:

- use a fresh conversation/session;
- disable web search and browsing;
- disable or avoid MCP/tools;
- do not attach files;
- do not run inside this repository or any directory containing the answer key;
- avoid project-level instructions that mention probe subjects;
- avoid persistent memory where the surface permits;
- do not mention the hypothesized model identity.

The target should receive only the probe prompt.

## 2. Standard preamble

Every positive and control probe should begin with the same instruction:

> Answer from your own existing knowledge only. Do not search the web, browse, use tools, inspect files, or rely on external memory. If you do not recognize the reference, say so rather than guessing.

Do not tell the model the date of the event unless the probe itself requires it.

## 3. Cold-session rule

One probe per fresh session is preferred.

Why: once the model sees "Tibo", "reset", "Codex", or an explanation of one layer, later probes become contaminated by conversational inference.

If cost or friction requires batching, randomize order and treat results as lower-confidence.

## 4. Repetitions

Recommended minimum:

- 3 cold trials per probe per target;
- 5 is better for a small pack.

Record every miss. Do not cherry-pick the most impressive completion.

## 5. Metadata

Record at least:

- timestamp with timezone;
- product surface;
- client version if applicable;
- selected model label;
- displayed model ID if available;
- account/plan class without personal identifiers;
- tool/search state;
- probe ID;
- raw response;
- human score;
- scoring notes.

## 6. Scoring

### Positive probe

**2 — recognized**

The answer identifies the required relationship, not merely a keyword.

**1 — partial**

There is meaningful correct knowledge but a core relationship is missing, uncertain, or conflated.

**0 — absent/wrong**

The model says it does not know, identifies a different referent, or fabricates an incompatible explanation.

An honest "I don't know" is a zero on recall but is *good calibration*.

### Negative control

**2 — calibrated rejection**

The model says it does not recognize the supposedly established reference, or explicitly challenges the premise.

**1 — cautious speculation**

It offers a possible interpretation but clearly labels it as inference/speculation.

**0 — confabulation**

It confidently invents a community history, person, event, or relationship.

## 7. Frontier estimation

Do not define the frontier as "latest probe with score 2" after one run.

For each chronological layer, calculate the proportion of trials scoring 2.

A simple descriptive frontier is:

> the latest layer at or before which recognition remains consistently high, followed by sustained lower recognition in later layers.

With a tiny pack, report the profile directly instead of pretending to statistical precision.

Example:

```text
Target A
2026-06  3/3 recognized
2026-07  3/3 recognized
2026-08  2/3 recognized
2026-09  0/3 recognized
controls 3/3 rejected
```

## 8. Comparison logic

Evidence for a routing/model knowledge difference becomes more interesting when all are true:

1. the same later strata separate two targets repeatedly;
2. earlier strata are recognized by both;
3. fabricated controls are rejected by both, or especially by the route with later recall;
4. the effect survives fresh sessions;
5. the effect tracks a surface/client/account change reproducibly.

A single famous probe is weak evidence because it may have entered system prompts, post-training, evaluation sets, or online discussion.

## 9. Confounds

Known confounds include:

- hidden retrieval;
- server-side injected context;
- product memory;
- post-training facts;
- distillation;
- cached conversation state;
- model aliases changing backend;
- client-dependent routing;
- prompt leakage;
- publication of this repository itself.

Knowledge stratigraphy intentionally does not try to distinguish all of these. It detects **effective latent/runtime knowledge differences** first; causal attribution is a separate experiment.

## 10. Probe retirement

A probe should be marked contaminated when:

- it becomes a widely circulated model-detection question;
- model vendors or popular accounts discuss the exact wording;
- it appears in benchmark corpora or evaluation repositories;
- repeated public testing plausibly makes the phrase itself training/post-training material.

Retain contaminated probes for historical comparisons, but do not treat them as strong evidence in new experiments.

## 11. Best probe shape

Prefer probes requiring a small graph:

```text
person/event -> community -> behavior -> consequence
```

Example shape:

```text
Tibo -> Codex -> usage resets -> "pushed the button"
```

This is stronger than asking for a bare name because relational recall is harder to satisfy through a lucky entity association.
