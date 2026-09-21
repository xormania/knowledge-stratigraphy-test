# Protocol

## Objective

Estimate and compare a target's **effective knowledge frontier** using dated, same-domain, closed-book probes.

A target is:

```text
Harness × Requested Model × Runtime
```

The protocol supports comparisons such as:

- same harness, different requested models;
- same requested model, different harnesses;
- same harness/model before and after a client update;
- same selected model label before and after suspected silent routing;
- requested model ID vs product alias;
- different reasoning/effort settings;
- future harnesses and future models.

The method does **not** establish backend identity. It measures behavioral evidence consistent with different effective knowledge.

## 1. Isolation

For every trial:

- use a fresh conversation/session where practical;
- disable web search and browsing;
- disable or avoid MCP/tools;
- do not attach files;
- do not run the target inside this repository or any directory containing answer keys;
- avoid project-level instructions that mention probe subjects;
- avoid persistent memory where the harness permits;
- do not mention the hypothesized model identity.

The target should receive only the probe prompt.

Record isolation conditions rather than assuming them.

## 2. Standard preamble

Every positive and control probe should begin with the same instruction:

> Answer from your own existing knowledge only. Do not search the web, browse, use tools, inspect files, or rely on external memory. If you do not recognize the reference, say so rather than guessing.

Do not tell the model the event date unless the probe itself requires it.

## 3. Cold-session rule

One probe per fresh session is preferred.

Once a target sees an explanation of one layer, later probes can become contaminated by conversational inference.

If cost or friction requires batching, randomize order and record that the trials share context.

## 4. Repetitions

Recommended minimum:

- 3 cold trials per probe per target;
- 5 is better for a small pack.

Record every result. Do not cherry-pick completions.

## 5. Target metadata

Record separately:

### Requested

- harness name;
- harness version if explicitly requested/pinned;
- requested model label/ID;
- requested provider/family;
- requested reasoning/effort;
- adapter and transport.

### Observed

When native evidence exists, also record:

- actual harness version/build;
- actual model label/ID;
- actual reasoning/effort;
- route/backend identity if exposed;
- evidence source;
- raw identity evidence.

**Requested is not observed.**

If effective identity cannot be established, record it as unknown.

## 6. Trial metadata

Also record:

- timestamp with timezone;
- target ID;
- pack ID/version;
- probe ID/order;
- exact prompt;
- raw response;
- latency/token usage when available;
- isolation state;
- comparison group/change event;
- human score and scoring notes.

## 7. Scoring

### Positive probe

**2 — recognized**

The answer identifies the required relationship, not merely a keyword.

**1 — partial**

There is meaningful correct knowledge but a core relationship is missing, uncertain, or conflated.

**0 — absent/wrong**

The model says it does not know, identifies a different referent, or fabricates an incompatible explanation.

An honest "I don't know" is a zero on recall but good calibration.

### Negative control

**2 — calibrated rejection**

The model says it does not recognize the supposedly established reference, or explicitly challenges the premise.

**1 — cautious speculation**

It offers a possible interpretation but clearly labels it as inference/speculation.

**0 — confabulation**

It confidently invents a history, person, event, term, or relationship.

## 8. Frontier estimation

Do not define the frontier as "latest probe with score 2" after one run.

For each chronological layer, calculate the proportion of trials scoring 2.

A simple descriptive frontier is:

> the latest layer at or before which recognition remains consistently high, followed by sustained lower recognition in later layers.

With a small pack, report the profile directly instead of pretending to statistical precision.

Example:

```text
Target A
2026-06  3/3 recognized
2026-07  3/3 recognized
2026-08  2/3 recognized
2026-09  0/3 recognized
controls 3/3 rejected
```

## 9. Comparison logic

Evidence for an effective-knowledge difference becomes more interesting when all are true:

1. the same later strata separate two targets repeatedly;
2. earlier strata are recognized by both;
3. fabricated controls are rejected rather than confidently invented;
4. the effect survives fresh sessions;
5. the effect tracks a model, harness, version, reasoning, or routing change reproducibly.

When trying to isolate one variable, hold the others constant where possible.

Examples:

```text
Harness A × Model X  vs Harness A × Model Y   -> model-oriented comparison
Harness A × Model X  vs Harness B × Model X   -> harness-oriented comparison
Harness A × Model X v1 vs same target v2       -> version/routing comparison
```

A single famous probe is weak evidence because it may have entered system prompts, post-training, evaluation sets, or online discussion.

## 10. Confounds

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
- local repository/context leakage;
- publication of the probes themselves.

Knowledge Stratigraphy does not initially try to distinguish all of these. It detects **effective latent/runtime knowledge differences** first; causal attribution is a separate experiment.

## 11. Probe retirement

A probe should be marked contaminated when:

- it becomes a widely circulated model-detection question;
- model vendors or popular accounts discuss the exact wording;
- it appears in benchmark/evaluation corpora;
- repeated public testing plausibly makes the phrase itself training/post-training material.

Retain contaminated probes for historical comparisons, but reduce or remove their weight in new experiments.

## 12. Best probe shape

Prefer probes requiring a small relation graph:

```text
entity/event -> domain/community -> behavior -> consequence
```

This is stronger than bare-name recognition because relational recall is harder to satisfy through a lucky entity association.

## 13. Execution universality

The protocol does not require a native adapter.

A **manual adapter** is always valid:

1. generate a blinded prompt;
2. open the chosen harness/model in a clean session;
3. submit the prompt;
4. capture the raw response;
5. capture any available native identity evidence;
6. append the trial telemetry.

Native adapters are an optimization for repeatability and richer evidence, not a prerequisite for supporting a harness/model.
