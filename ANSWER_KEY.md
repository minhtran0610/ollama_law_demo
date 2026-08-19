# Ground-truth answer key

For sanity-checking the live model output against. Sourced directly from the law
texts, not from a model run.

## Question 1 (32K) — bachelor's graduate → permanent residence permit

Source: `law_texts/aliens_act_amendments.txt` only. Amendments apply to permanent-RP
applications submitted on or after **8 January 2026** (today is 2026-08-18, so this
governs).

Five application paths, all requiring "other permit requirements" to also be met:

| Path | Residence period | Work history | Language | Notes |
|---|---|---|---|---|
| Residence of 6 years | 6 yr continuous permit | 2 yr | B1 (waived at 65+) | the new standard route |
| Annual income €40,000 | 4 yr continuous permit | *not stated in text* | *not stated in text* | just residence + income per the source |
| **Higher ed degree completed in Finland** | **none** | **none** | **A2 or 15 credits** | Master's (university or UAS), licentiate, doctorate, **or bachelor's — university only, NOT university of applied sciences** |
| Degree completed outside Finland | 4 yr | 2 yr | *not stated* | degree must be master's/licentiate/doctorate recognized in Finland |
| Particularly good language skills | 4 yr | 3 yr | C1 | |

**The point of the question**: a bachelor's degree from a Finnish *university* (not
UAS) waives the residence-period requirement entirely — a dramatic, easy-to-miss fact
that only exists in the amendment text, not in the base `aliens_act.txt` (which still
shows the pre-2026 flat 4-year rule at §56 and says nothing about degree-based
fast-tracks).

**Known reliability issue — rehearse for this**: across repeated test runs (all at full
32K context, no truncation involved), this specific fact flips between "none" and
"4 years" roughly 1 time in 3, regardless of thinking mode. This is sampling variance
from the model's baked-in `temperature: 1`, not a context problem — `prompt_eval_count`
was well within budget in every one of these runs. A `temperature: 0.2` override was
tried to suppress this and made things *worse* (the model fell into a verbatim
repetition loop and never reached an answer at all), so the script intentionally leaves
temperature at the model's default. If the live run gets it wrong, don't treat it as a
context-length failure — say so and rerun, or use it as a separate teaching moment about
sampling variance vs. context truncation being two different failure modes.

**Distractor added**: `aliens_act.txt` Chapter 6 "International protection" (asylum/
refugee, ~10.4K tokens) is now included alongside the amendments file, bringing the
corpus to ~23.75K tokens (72% of 32K, still comfortably under budget). It's real,
substantial, genuinely mentions residence permits throughout, and is completely
irrelevant to a bachelor's graduate's permanent-RP question. Confirmed in testing:
the model correctly ignored it entirely — zero mentions of asylum/refugee content in
the answer — while still nailing the degree-based zero-residence-period fact.

**Known trap in the source text**: the €40,000-income path's own bullet mentions no
language or work-history requirement at all — don't let the model quietly invent a
"B1 implied" requirement there. In one 32K test run it did exactly that, hedging
instead of saying "not stated in the text" as the system prompt instructs. Worth
pointing out live if it happens again — a clean example of a model filling a gap
against its own instructions, not a context-length failure.

## Question 2 (128K) — non-EU solo founder → entrepreneur RP → permanent RP

Source: Aliens Act ch.1/4/5 + LLC Act ch.1/2/3/5/6/7/8/9 + Companies Act amendments
supplement (~61,226 tokens total). LLC Act chapters are deliberately ordered
"ballast first, needed-last" — ch.3/5/7/8/9 (not required to answer the question)
come before ch.2/1/6 (incorporation, capital, board residency — the chapters the
question actually needs). This is still whole-chapter-only, nothing is cut
mid-chapter; only the chapter *order* is chosen.

**Why the reordering matters**: Ollama's truncation on overflow keeps the *tail*
of the prompt and drops the front (confirmed via a direct canary test — a marker
sequence 1–699 at 2x context overflow returned only markers 661–699 visible, i.e.
only the last ~50% of num_ctx survives, counted from the end backward). Since
Aliens Act sits first in the corpus, growing the LLC Act block to ~30K pushes the
32K survival window entirely past Aliens Act — dropping all of it, cleanly — while
still landing inside the reordered LLC block late enough to keep ch.2/1/6 intact.

**Confirmed behavior at 32K** (`prompt_eval_count=16,386`, ~44,840 tokens dropped):
Aliens Act is 100% absent from what the model sees. A correct, well-behaved answer
should say so explicitly rather than answering part 1 (entrepreneur RP requirements)
from training knowledge. One real run did exactly this: *"Residence permits are
governed by the Aliens Act, not this text."* — a good outcome to point at live.

**Watch for this instead**: the same run still slipped in *"proof of sufficient
paid-up equity (often €50k+ under Aliens Act rules)"* — a specific fabricated
figure attributed to a document that was not in context at all that run. This is
a stronger "gotcha" than a vague wrong answer: a concrete, confident, sourced-sounding
number that came from nowhere in the provided text. If it recurs, it's the single
best thing to point at on stage — proof the model is drawing on pretraining, not
your corpus, while still using "Aliens Act" as if it were citing it.

**Correction — NOT a truncation artifact**: earlier testing attributed the LLC Act
"Chapter 1, Section 10" vs "Chapter 6, Section 10" mislabeling (board EEA-residency
requirement) to truncation dropping a chapter heading. A run where *both* the real
Chapter 1 §10 (listed-company definition) and the real Chapter 6 §10 (EEA residency)
were fully present in context still produced the same mislabeling. So this specific
error is the model conflating two same-numbered sections from different chapters —
a reading-comprehension slip independent of context length. Don't attribute it to
truncation if it comes up; it can happen at 128K too.

**1. Residence permit for an entrepreneur (Aliens Act §79/§79a)**
- Business activities take place in a company registered in Finland.
- Business meets requirements for profitable business.
- Company has sufficient resources to operate.
- Taxes/charges not materially neglected.
- The Centre for Economic Development, Transport and the Environment (ELY Centre)
  issues a favourable *partial decision* first; that decision sets whether the permit
  is temporary or continuous. The Finnish Immigration Service issues the permit itself.
- Financial resources during the early stage can come from gainful employment, initial
  company funding, or the applicant's own funds (§79a).

**2. EEA-residency catch-22 for a solo founder (LLC Act §10, §19)**
- At least one board member must be EEA-resident, unless the registration authority
  (Patent and Registration Office / PRH) grants an exemption.
- The managing director must *always* be EEA-resident, unless the registration
  authority grants an exemption — this applies even if not required for board members.
- A non-EU founder who is not yet EEA-resident cannot alone satisfy both roles without
  either (a) bringing in an EEA-resident co-founder/board member, or (b) obtaining a
  PRH exemption. This is the "aha" of the question — easy to miss without reading
  the LLC Act's Chapter 6 in full.

**3. Minimum share capital (LLC Act §3)**
- Public company: €80,000 minimum.
- Private company (Oy): **no minimum share capital stated** — a common misconception
  is that a small minimum still applies post-2019 reform; it doesn't.

**4. Recent company-law amendments — do they matter here?**
- Act 1252/2023 / Act 558/2026 (CSRD sustainability reporting): thresholds now
  >1,000 employees and >€450M turnover — irrelevant to a solo consultancy.
- Act 652/2024 (board gender balance): applies only to *listed* companies — the
  amendment text itself says so explicitly. Irrelevant to a private non-listed Oy.
- **Correct answer: none of the 2023–2026 amendments affect this founder's situation.**
  Watch for the model correctly saying this rather than treating "recent amendment"
  as automatically relevant just because it's in the context.

**5. Path from entrepreneur RP to permanent RP (Aliens Act §56 + the 2026 amendment)**
- `aliens_act_amendments.txt` is now included in Q2's corpus too (added after the
  original design), positioned with the other Aliens Act material — i.e. still
  entirely inside the "always dropped at 32K" block, so this doesn't change the
  32K-vs-128K story, just adds a reconciliation test at 128K.
- **Correct answer requires recognizing BOTH documents and knowing which governs**:
  the base act's §56 sets the old flat 4-year rule; the amendment (in force for
  applications submitted on/after 8 January 2026) supersedes it with the same five
  paths documented in Question 1's answer key (6yr standard / 4yr+€40k income /
  degree-based zero-residence / degree-outside-Finland / C1 language). Since today
  is 2026-08-18, **the amended rules govern** — a correct answer should say so
  explicitly, not just recite §56's superseded 4-year figure.
- Confirmed in testing (128K, `prompt_eval_count=74,917`, no truncation): the model
  correctly cited both §56 (old) and the 8 Jan 2026 press release (new), explicitly
  said the new rule applies for applications on/after that date, and correctly
  surfaced the €40k income exemption. It only mentioned the master's-degree
  exemption though, not Question 1's bachelor's-at-university nuance — not wrong,
  just less complete than Question 1's dedicated treatment of the same fact.
- Minor fabrications seen in testing, worth watching for: a citation to *"Aliens
  Act Ch. 69b–69f"* for an "outsourcing residence permit tasks" provision, and
  *"continuous entrepreneur residence permit (Letter A in Chapter 34)"* — neither
  matches anything in this corpus (Ch.1/4/5 only go into the 80s for section
  numbers; there is no "Chapter 34").
