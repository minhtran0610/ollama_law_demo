# Ollama context-window demo

A live demo for the Vietnamese tech community in Finland, showing what actually
happens when you hand a local LLM more real-world text than its context window
can hold — using content the audience will genuinely care about: Finnish
residence permit rules and how to set up a limited liability company (Oy) as a
non-EU founder.

Everything runs locally through [Ollama](https://ollama.com), on real,
unmodified Finnish statute translations (Aliens Act, Limited Liability
Companies Act) plus their 2023–2026 amendment supplements.

## The headline finding

It's common to assume that if a prompt is bigger than a model's context
window, you just lose "the overflow" — the tail end gets cut, everything else
survives. That's not what happens in practice.

Measured directly against this setup: **when a prompt exceeds Ollama's
`num_ctx` budget, it doesn't keep as much as fits — it silently drops down to
roughly half the configured window**, no error, no warning. A prompt that's
25% over budget and a prompt that's 400% over budget both get cut to the same
~50%. The only way to know how much of your context survived is to check the
API's `prompt_eval_count` after the fact — which is exactly what this demo
makes visible on screen, instead of just asserting it.

The three segments below build on that one mechanism, using progressively
more of it.

## Prerequisites

- [Ollama](https://ollama.com) installed and running (`ollama serve`), tested
  against Ollama 0.32.x.
- [uv](https://docs.astral.sh/uv/) for Python dependency management.
- A GPU with enough VRAM to hold a 9B q4 model comfortably at up to 256K
  context (KV cache size scales with context length). Tested on an
  RTX 4070 Ti Super (16 GB).
- Model pulled:
  ```
  ollama pull qwen3.5:9b-q4_K_M
  ```
- For the interactive 256K segment, a second tag with a bigger context baked
  into its Modelfile (same weights, same sampling parameters, just a larger
  `num_ctx` default so you don't have to set it by hand mid-demo):
  ```
  cat <<'EOF' > Modelfile.256k
  FROM qwen3.5:9b-q4_K_M
  PARAMETER num_ctx 262144
  EOF
  ollama create qwen35-9b-q4km-256k -f Modelfile.256k
  ```

Then, from the repo root:
```
uv sync
```

## The three segments

### 1. Warm-up (32K, fits cleanly): "I'm about to graduate — what's my fastest path to permanent residence?"

Source material: the Aliens Act's 2023–2026 amendments supplement, plus a
real, unrelated chapter of the base Aliens Act (asylum/refugee law) mixed in
as noise. ~23.8K tokens, 72% of a 32K window — comfortably fits, nothing
truncated.

The payoff: a January 2026 amendment most people haven't caught up on yet —
completing a **bachelor's degree at a Finnish university** (not a university
of applied sciences) waives the residence-period requirement for a permanent
residence permit entirely. The model has to find that fact, correctly ignore
the unrelated asylum-law chapter sitting right next to it, and get the
university-vs-UAS distinction right.

```
uv run ollama-law-demo 1 32k
```

### 2. The main event (32K fails, 128K works): "I want to start a tech consultancy as a non-EU founder and eventually get permanent residence"

Source material: the Aliens Act's entrepreneur-permit and residence chapters,
the Limited Liability Companies Act's incorporation/capital/board-management
chapters, and both acts' amendment supplements — real content only, no
padding. ~74.6K tokens total.

- At **32K**, that's more than double the budget. The model gets truncated
  down to ~16K tokens and — in testing — has *zero* visibility into the
  Aliens Act portion of the material at all. A well-behaved answer says so
  explicitly instead of quietly filling the gap from its own training data;
  watching whether it does that live is the point.
- At **128K**, the same ~74.6K tokens is only 57% of budget — everything
  fits, and the answer can correctly synthesize both acts: the entrepreneur
  permit's requirements, the EEA-residency catch-22 for a solo non-EU board
  member, that a private Oy has no statutory minimum share capital (only
  public companies do), and which of the recent company-law amendments
  actually apply (usually none, for a small private company).

```
uv run ollama-law-demo 2 32k
uv run ollama-law-demo 2 128k
```

Useful flags on both commands: `--dry-run` (show the token budget without
calling the model), `--model {9b,4b,2b,0.8b}` (switch model size, default
`9b`; all pulled locally -- 9b/4b/2b at q4_K_M, 0.8b at q8_0), `--num-predict N`
(generation budget; question 2 tends to need less than question 1),
`--hide-thinking` (skip streaming the model's reasoning, answer only).

### 3. Interactive: hand it to the audience (128K per act, 256K combined)

No script, no pre-written question — this is where the audience asks
whatever they actually want to know.

Two ready-to-paste files, each the **complete, unmodified act translation
plus its own amendments supplement** (no trimming needed — at this context
size there's real headroom to spare):

| File | Tokens | % of 128K |
|---|---|---|
| `law_texts/aliens_act_interactive.txt` | ~89.9K | 68% |
| `law_texts/llc_act_interactive.txt` | ~70.6K | 54% |
| both, combined | ~160.5K | 61% of 256K |

Live flow, on the `qwen35-9b-q4km-256k` tag throughout so there's no model
swap mid-demo:

```
ollama run qwen35-9b-q4km-256k
/set parameter num_ctx 131072
<paste law_texts/aliens_act_interactive.txt, then type the audience's residence-permit question>

/clear
/set parameter num_ctx 131072
<paste law_texts/llc_act_interactive.txt, then type the audience's company-law question>

/clear
/set parameter num_ctx 262144
<paste both files into the same conversation, then ask a combined question that needs both acts — e.g. "how does someone actually go from starting a company to getting permanent residence?">
```

Terminal paste of a large block usually arrives as one operation (not
submitted line-by-line) in modern terminal emulators — worth a quick
rehearsal paste beforehand to confirm yours behaves the same way. To
regenerate these two files after any change to the source law texts:

```
uv run python scripts/export_interactive_context.py
```

## Repo layout

```
law_texts/            Source material: official act translations, amendment
                       supplements, and the two exported interactive files
scripts/
  context_demo.py      The scripted 32K/128K demo (segments 1 and 2)
  export_interactive_context.py   Regenerates the two interactive files
  fetch_amendments.py  Re-scrapes the Aliens Act amendment press releases
  extract_finlex_pdf.py  Extracts text from a Finlex statute PDF
ANSWER_KEY.md          Presenter's rehearsal notes: ground truth for both
                       scripted questions, plus specific model behaviors
                       (and a couple of known quirks) observed while testing
```

## A note on reliability

This is a real, non-deterministic language model, not a scripted trick — the
same question can land slightly differently between runs (sampling
temperature is left at the model's default rather than forced down, since a
low-temperature attempt to reduce variance was tested and made things worse,
causing repetition loops instead). `ANSWER_KEY.md` documents the expected
correct answer for each scripted question and a couple of specific behaviors
worth watching for, so a run that drifts from the ideal can be caught and
explained live rather than come as a surprise.
