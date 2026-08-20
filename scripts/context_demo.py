#!/usr/bin/env python3
"""Live demo: same question, different Ollama num_ctx budgets, real law text as context.

Usage:
  python context_demo.py 1 32k          # bachelor's-degree permanent-RP question, should fit cleanly
  python context_demo.py 2 32k          # entrepreneur/company-formation question, should overflow
  python context_demo.py 2 128k         # same question, should fit cleanly
  python context_demo.py 2 128k --dry-run   # just show corpus stats, don't call the model

Ollama's real behavior (verified empirically against this machine's qwen3.5:9b-q4_K_M):
  - If the prompt fits inside num_ctx: it's processed in full, no loss.
  - If the prompt exceeds num_ctx: Ollama silently truncates to roughly num_ctx / 2,
    not "as much as fits". No error, no warning. This script measures and reports the
    real prompt_eval_count from the API response so the truncation is visible on stage,
    not just asserted.
"""
import argparse
import json
from pathlib import Path

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

LAW_TEXTS = str(Path(__file__).resolve().parent.parent / "law_texts")
MODEL = "qwen3.5:9b-q4_K_M"
OLLAMA_URL = "http://localhost:11434/api/chat"

CTX_SIZES = {"32k": 32768, "128k": 131072}

# Chapter line ranges (1-indexed, inclusive), cut along the Act's own chapter
# headings only -- no cherry-picking inside a chapter. Ranges found via:
#   grep -n -E "^Chapter " law_texts/<file>.txt
ALIENS_CH1 = (13, 403)      # General provisions
ALIENS_CH4 = (840, 2534)    # Residence (incl. extended/permanent permits, S54-56a)
ALIENS_CH5 = (2535, 3481)   # Employment and pursuing a trade (incl. entrepreneur RP, S79-80b)
ALIENS_CH6 = (3482, 4612)   # International protection (asylum/refugee -- distractor for Q1,
                             # irrelevant to a bachelor's-graduate permanent-RP question but
                             # genuinely mentions residence permits throughout)

LLC_CH1 = (13, 196)         # Main principles (incl. S3 minimum share capital)
LLC_CH2 = (197, 432)        # Incorporation of a limited liability company
LLC_CH3 = (433, 947)        # Shares
LLC_CH5 = (948, 1742)       # General meeting (ch.4 was repealed, numbering skips it)
LLC_CH6 = (1743, 2285)      # Management and representation (incl. S10/S19 EEA residency)
LLC_CH7 = (2286, 2420)      # Audit and special audit
LLC_CH8 = (2421, 2637)      # Equity, financial statements, management report and group
LLC_CH9 = (2638, 2968)      # Share issue

# tokens-per-byte, measured against this file's own full-text prompt_eval_count
# (used only to print a pre-flight estimate for the chapter slices below; the real
# count for the actual call comes from the API's prompt_eval_count after it runs)
ALIENS_RATIO = 76426 / 348079
LLC_RATIO = 68297 / 332608

# whole files are used unsliced -- their exact token counts were already measured
# directly (num_predict=0 probe), so no ratio estimate is needed for these two
ALIENS_AMENDMENTS_TOKENS = 13340
COMPANIES_AMENDMENTS_TOKENS = 2194


def nbytes(text):
    return len(text.encode("utf-8"))


def read_lines(path, start, end):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    return "".join(lines[start - 1 : end])


def read_whole(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build_corpus(question):
    """Returns (system_preamble, [(label, text, est_tokens), ...])."""
    docs = []
    if question == 1:
        aliens_path = f"{LAW_TEXTS}/aliens_act.txt"
        ch6 = read_lines(aliens_path, *ALIENS_CH6)
        docs.append(("Aliens Act ch.6 International protection (distractor)", ch6, nbytes(ch6) * ALIENS_RATIO))

        text = read_whole(f"{LAW_TEXTS}/aliens_act_amendments.txt")
        docs.append(("Aliens Act -- amendments supplement (whole file)", text, ALIENS_AMENDMENTS_TOKENS))
    else:
        aliens_path = f"{LAW_TEXTS}/aliens_act.txt"
        llc_path = f"{LAW_TEXTS}/limited_liability_companies_act.txt"

        ch1 = read_lines(aliens_path, *ALIENS_CH1)
        ch4 = read_lines(aliens_path, *ALIENS_CH4)
        ch5 = read_lines(aliens_path, *ALIENS_CH5)
        docs.append(("Aliens Act ch.1 General provisions", ch1, nbytes(ch1) * ALIENS_RATIO))
        docs.append(("Aliens Act ch.4 Residence", ch4, nbytes(ch4) * ALIENS_RATIO))
        docs.append(("Aliens Act ch.5 Employment & entrepreneurship", ch5, nbytes(ch5) * ALIENS_RATIO))

        amendments = read_whole(f"{LAW_TEXTS}/aliens_act_amendments.txt")
        docs.append(("Aliens Act -- amendments supplement (whole file)", amendments, ALIENS_AMENDMENTS_TOKENS))

        # Ollama truncates prompt overflow by keeping the TAIL of the prompt and
        # dropping the front (confirmed empirically -- see conversation notes).
        # Aliens Act sits first in this corpus, so at 32K it gets dropped entirely.
        # Within the LLC Act block, "ballast" chapters (not needed to answer the
        # question) go first so they absorb the drop; the chapters the question
        # actually needs go last, closest to the surviving tail. Still whole
        # chapters only -- nothing is cut mid-chapter, only reordered.
        ballast_ranges = [
            ("LLC Act ch.3 Shares", LLC_CH3),
            ("LLC Act ch.5 General meeting", LLC_CH5),
            ("LLC Act ch.7 Audit and special audit", LLC_CH7),
            ("LLC Act ch.8 Equity, financial statements & group", LLC_CH8),
            ("LLC Act ch.9 Share issue", LLC_CH9),
        ]
        for label, rng in ballast_ranges:
            text = read_lines(llc_path, *rng)
            docs.append((label, text, nbytes(text) * LLC_RATIO))

        needed_ranges = [
            ("LLC Act ch.2 Incorporation", LLC_CH2),
            ("LLC Act ch.1 Main principles", LLC_CH1),
            ("LLC Act ch.6 Management & representation", LLC_CH6),
        ]
        for label, rng in needed_ranges:
            text = read_lines(llc_path, *rng)
            docs.append((label, text, nbytes(text) * LLC_RATIO))

        amend = read_whole(f"{LAW_TEXTS}/companies_act_amendments_2023_2026.txt")
        docs.append(("Companies Act amendments 2023-2026 supplement (whole file)", amend, COMPANIES_AMENDMENTS_TOKENS))

    return docs


QUESTIONS = {
    1: (
        "I'm a non-EU citizen finishing my Bachelor's degree in Finland this year. "
        "Once I graduate, what is the fastest legitimate path to a permanent residence "
        "permit, and exactly what conditions do I need to meet? Compare it against the "
        "standard route and any other route that might apply to a recent graduate. "
        "Be precise about which routes require which degree level and which institution "
        "type qualifies."
    ),
    2: (
        "I'm a non-EU citizen currently living in Finland on a student residence permit. "
        "I want to set up my own one-person limited liability company (Oy) as a tech "
        "consultant, switch my residence status to a residence permit for an entrepreneur, "
        "and eventually qualify for a permanent residence permit. Walk me through: (1) what "
        "I need to satisfy to get the residence permit for an entrepreneur, and whether "
        "switching from my current student permit requires me to leave Finland and reapply "
        "from abroad, or can be done from inside the country, (2) any company-law "
        "requirement or obstacle specific to being a non-EU/non-EEA founder setting this up "
        "alone, (3) the minimum share capital I need, (4) whether any recent company-law "
        "amendments in the material affect my situation, and (5) once I hold the "
        "entrepreneur residence permit, what the actual path and requirements are to "
        "eventually get a permanent residence permit."
    ),
}

SYSTEM_PREAMBLE = (
    "You are answering strictly from the Finnish statutory text provided below in the "
    "context window. Cite section numbers when you rely on them. If the provided text "
    "does not fully cover part of the question, say so explicitly rather than filling "
    "the gap from general knowledge. If a later amendment in the provided text changes "
    "or supersedes an earlier provision, say which one governs and why."
)


def format_corpus(docs):
    parts = []
    for label, text, _ in docs:
        parts.append(f"===== {label} =====\n{text}")
    return "\n\n".join(parts)


def run(question, ctx_key, num_predict, show_thinking, dry_run, temperature):
    num_ctx = CTX_SIZES[ctx_key]
    docs = build_corpus(question)
    corpus_text = format_corpus(docs)
    est_tokens = sum(t for _, _, t in docs)

    console = Console()
    console.print(f"[bold]=== Question {question} @ {ctx_key} (num_ctx={num_ctx}) ===[/bold]")
    console.print(f"Model: {MODEL}")
    for label, text, est in docs:
        console.print(f"  - {label}: {nbytes(text):>8,} bytes  (~{est:>7,.0f} est. tokens)")
    console.print(f"Corpus estimate: ~{est_tokens:,.0f} tokens vs budget {num_ctx:,}")
    if est_tokens > num_ctx:
        console.print(
            f"  [bold yellow]>> OVER BUDGET:[/bold yellow] Ollama will silently truncate to roughly "
            f"{num_ctx // 2:,} tokens, not '{num_ctx:,} minus overflow'. Watch prompt_eval_count below."
        )
    else:
        console.print(f"  [bold green]>> fits[/bold green], {est_tokens / num_ctx * 100:.0f}% of budget used")
    console.print()

    if dry_run:
        return

    messages = [
        {"role": "system", "content": SYSTEM_PREAMBLE + "\n\n" + corpus_text},
        {"role": "user", "content": QUESTIONS[question]},
    ]
    options = {"num_ctx": num_ctx, "num_predict": num_predict}
    if temperature is not None:
        options["temperature"] = temperature
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "think": show_thinking,
        "options": options,
    }

    in_thinking = False
    in_answer = False
    answer_buffer = ""
    prompt_eval_count = None
    eval_count = None
    done_reason = None
    with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=600) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            chunk = json.loads(line)
            msg = chunk.get("message", {})
            thinking = msg.get("thinking")
            content = msg.get("content")
            if thinking:
                if not in_thinking:
                    console.print()
                    console.print(Rule("thinking", style="dim"))
                    in_thinking = True
                console.print(thinking, style="dim", end="", markup=False, highlight=False)
            if content:
                if not in_answer:
                    if in_thinking:
                        console.print()
                    console.print()
                    console.print(Rule("answer (streaming raw)", style="bold green"))
                    in_answer = True
                    in_thinking = False
                # plain streaming -- no live re-render, so it's immune to the
                # cursor-math corruption Live hits once content outgrows the
                # visible terminal height
                console.print(content, end="", markup=False, highlight=False)
                answer_buffer += content
            if chunk.get("done"):
                prompt_eval_count = chunk.get("prompt_eval_count")
                eval_count = chunk.get("eval_count")
                done_reason = chunk.get("done_reason")

    if answer_buffer:
        console.print()
        console.print()
        console.print(Rule("answer (rendered)", style="bold green"))
        console.print(Markdown(answer_buffer))

    console.print()
    console.print(f"=== stats: prompt_eval_count={prompt_eval_count:,} (actual tokens the model saw) "
                   f"eval_count={eval_count:,} (tokens generated) done_reason={done_reason} ===")
    if prompt_eval_count is not None and est_tokens > prompt_eval_count * 1.05:
        dropped = est_tokens - prompt_eval_count
        console.print(f"  >> confirmed: ~{dropped:,.0f} tokens of the intended corpus were dropped before the model ever saw them.")
    if done_reason == "length" and eval_count == num_predict:
        print(f"  >> stopped because it hit --num-predict {num_predict}, not because of the context budget "
              f"(prompt only used {prompt_eval_count:,}/{num_ctx:,}). Rerun with a higher --num-predict "
              f"if you want to see the final answer, not just the reasoning.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", type=int, choices=[1, 2])
    ap.add_argument("ctx", choices=list(CTX_SIZES))
    ap.add_argument("--num-predict", type=int, default=12000,
                     help="max tokens to generate (thinking + answer combined); Q1 needs 12k+ to reach a final answer")
    ap.add_argument("--hide-thinking", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="show corpus stats only, don't call the model")
    ap.add_argument("--temperature", type=float, default=None,
                     help="override the model's baked-in default (1.0); omit to use the model's own default "
                          "(0.2 was tried and caused repetition loops -- not recommended)")
    args = ap.parse_args()

    run(args.question, args.ctx, args.num_predict, not args.hide_thinking, args.dry_run, args.temperature)


if __name__ == "__main__":
    main()
