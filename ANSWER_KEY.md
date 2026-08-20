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

**New trap 1 — ordinary entrepreneur (§79) vs. startup entrepreneur (§80)**: the
question says "tech consultant," which invites the model to reach for the *startup*
entrepreneur permit (§80/§80a) since "tech" reads as innovative. That route requires a
favourable statement from the Innovation Funding Agency **Business Finland**, which
assesses whether the business model shows potential for *rapid international growth*
— confirmed against Business Finland's and Migri's own public guidance, not just this
corpus. A one-person consultancy trading hours for money doesn't inherently clear that
bar; it's the ordinary §79 ELY-Centre route (profitable business + sufficient
resources + taxes not neglected), not §80. A correct answer either states this
distinction explicitly or at minimum answers under §79 without conflating it with the
Business Finland/startup route. Citing §80 as if it were the applicable path, or
blending its requirements (Business Finland statement, rapid-growth business model)
into a §79 answer, is the failure mode to watch for.

**Confirmed in testing (128K, `prompt_eval_count=74,954`, no truncation, revised
student-permit question wording):** the model answered entirely under §79/§79a and
never mentioned §80, "startup entrepreneur," or Business Finland — it did not fall
into the trap this run. Worth a few more runs before the demo to see how often it
holds, since sampling variance is a known factor for this model (see Question 1's
notes on the degree-based fact flipping ~1 in 3 runs).

**New trap 2 — does switching from a student permit require leaving Finland? (§54,
§60)**: §60 subsection 1 requires a **first** residence permit to be applied for from
abroad, before entering Finland — entrepreneur/startup-entrepreneur permits are not on
the short list of exceptions that may be filed from inside the country. But §54
("Issue of extended permits") allows "a new fixed-term residence permit ... on new
grounds if such grounds would qualify the alien for the first residence permit" — i.e.
someone who already holds a permit (here, the student permit) can pivot their purpose
of stay to entrepreneurship as an **extended permit**, and §60 subsection 2 says
extended permits "shall be applied for in Finland." **Correct answer: since the
applicant already holds a Finnish residence permit, they do not need to leave the
country — they apply for the switch from inside Finland, provided the §79/§79a
entrepreneur requirements are otherwise met.** The tempting wrong answer — "you must
leave and reapply from a Finnish mission abroad, like a brand-new applicant" — is a
belief plausible enough that it's worth calling out by name if the model produces it.

**Confirmed in testing (128K, `prompt_eval_count=74,954`, no truncation, revised
student-permit question wording):** the model failed this trap. It found §60(1)
(first permit → apply abroad) and even quoted §60(2) ("extended permit... shall be
applied for in Finland") in its own thinking, but never located or cited §54's "new
grounds" clause, the piece that actually resolves the question. It landed on "you
would likely need to leave Finland and apply abroad," hedged as an "important
ambiguity," rather than correctly concluding the switch can be filed in Finland. Good
one to watch for live — the model had all the raw material (§54 and §60 are both in
Chapter 4, well within the 128K budget) but didn't connect them.

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
- **Regression seen in a later run (128K, `prompt_eval_count=74,954`, no truncation,
  revised student-permit question wording)** — a clean example of the same
  sampling-variance problem Question 1 has, just showing up here instead: the model
  collapsed the amendment's five paths into one blanket rule ("six years, B1 language,
  two years' work history") and:
  - Never mentioned the **A2-or-15-credits** language level that applies specifically
    to the higher-ed-in-Finland route (line 199 of `aliens_act_amendments.txt`) —
    presented B1 as if it were the only language bar, when B1 only governs the
    6-year standard route.
  - **Completely omitted the €40,000-income path** (4 years, no stated language or
    work-history requirement) — the exact same fact Question 1's answer key already
    flags as a known trap the model sometimes misses. "40,000" / "€40" does not
    appear anywhere in this run's answer.
  - This is not a corpus or truncation issue — `prompt_eval_count` shows nothing was
    dropped. It's the model treating the amendment as one unified rule instead of
    five distinct paths, same failure class as Question 1's degree-fact flip. Worth
    rerunning a couple of times before the demo; if it recurs, it's a good live
    teaching moment about the model under-using a big context window it *did*
    receive in full, rather than a truncation story.
