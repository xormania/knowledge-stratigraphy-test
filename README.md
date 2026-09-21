# Knowledge Stratigraphy Test

A black-box method for estimating an LLM's **effective knowledge frontier** and detecting silent model/routing changes.

The core idea: do not rely on one obscure fact. Probe a **dated sequence of obscure, relational facts from the same community**, add fabricated controls, repeat in cold sessions, and compare the shape of what the model knows.

This is not an intelligence benchmark and cannot prove a backend model identity. It is a fingerprinting experiment.

## Why "stratigraphy"?

Published knowledge cutoffs are useful, but model knowledge is not a clean geological boundary. Facts can enter through pretraining, continued pretraining, post-training, distillation, runtime context, retrieval, or other mechanisms.

So this project measures an **effective knowledge frontier**:

> How far into a dated sequence of niche public knowledge does the model appear to have reliable latent knowledge when retrieval and external context are removed?

The pattern across layers matters more than any individual answer.

## v0 target

The first pack uses **Codex reset lore from June through September 2026**.

That vein is useful because it is:

- narrow enough to hold subject matter mostly constant;
- rich in dated, public events;
- obscure enough that recognition is meaningful;
- relational rather than simple headline trivia;
- especially interesting around late June 2026.

Anthropic documents Claude Fable 5.1 with a reliable/training knowledge cutoff of **June 2026**. The pack deliberately crosses that boundary.

## Files

- `probes/codex-reset-2026-v0.1.json` — versioned probe definitions and answer signals.
- `PROTOCOL.md` — experimental procedure and interpretation.
- `EVIDENCE.md` — public evidence used to construct the pack.
- `stratify.py` — zero-dependency helper for listing, blinding, and revealing probes.
- `results/` — suggested location for human-recorded runs.

## Quick start

List the pack:

```bash
python3 stratify.py list
```

Print one blinded prompt:

```bash
python3 stratify.py prompt KST-2026-09-12
```

Print a randomized blinded battery:

```bash
python3 stratify.py batch --seed 42
```

Reveal a probe only after collecting the answer:

```bash
python3 stratify.py reveal KST-2026-09-12
```

## Critical rule

**Do not run the target model from inside this repository.**

Claude Code, Codex, and other agents may read local files. If the target can inspect this repo, the answer key is contaminated.

Generate/copy the blinded prompts, then run them in fresh sessions outside the repo with web/search/tools/project memory disabled as far as the surface permits.

## Scoring

Positive probes:

- **2** — recognizes the core relationship and context.
- **1** — partial recognition, with meaningful correct signal.
- **0** — unknown, wrong, or unrelated association.

Negative controls:

- **2** — rejects the invented reference or explicitly does not recognize it.
- **1** — offers a hypothesis but clearly labels it as speculation.
- **0** — confidently fabricates lore around the fake reference.

Do not reward verbosity.

## What a useful result looks like

Not:

> It knew Tibo, so it must be Model X.

Better:

> Across a dated same-domain sequence, Route A's reliable recall extends materially later than Route B's over repeated cold sessions, while Route A also rejects fabricated controls.

A profile might look like:

```text
June      ██████████
July      ██████████
August    ████████░░
September ████░░░░░░
Controls  ██████████
```

A coherent temporal transition is more informative than one isolated hit.

## Contamination is expected

Once a probe becomes a popular model-detection meme, it stops being a clean probe.

Packs should be:

- versioned;
- source-grounded;
- retired when contaminated;
- replaced with new same-domain strata.

The framework is the durable artifact. The trivia is disposable.

## Origin

The project grew from the community's use of **"Tibo the reset guy"** as an accidental black-box model fingerprint. Knowledge stratigraphy generalizes that observation into a controlled, dated battery.
