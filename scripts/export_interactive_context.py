#!/usr/bin/env python3
"""Export the FULL Aliens Act and FULL LLC Act (each + its own amendments
supplement, no chapter trimming) as two standalone .txt files, for pasting
directly into an interactive `ollama run` session so the audience can ask
their own live question -- no fixed script, no pre-written prompt.

Sizing (measured against the real qwen3.5 tokenizer):
  aliens_act_interactive.txt  ~89,766 tokens  (68% of a 128K window)
  llc_act_interactive.txt     ~70,491 tokens  (54% of a 128K window)
  combined                   ~160,257 tokens  (61% of a 256K window)

Usage:
  python export_interactive_context.py

Suggested live flow, all on the qwen35-9b-q4km-256k model (same sampling
params as the base model, just a bigger baked-in context) so there's no
mid-demo model swap:
  1. ollama run qwen35-9b-q4km-256k
  2. /set parameter num_ctx 131072
  3. paste aliens_act_interactive.txt, then ask any residence-permit question
  4. /clear
  5. /set parameter num_ctx 131072
  6. paste llc_act_interactive.txt, then ask any company-law question
  7. /clear
  8. /set parameter num_ctx 262144
  9. paste aliens_act_interactive.txt, then llc_act_interactive.txt (same
     conversation, both pasted in), then ask a combined entrepreneur-RP
     question that needs both acts
  Terminal paste of a large block usually arrives as one bracketed paste (no
  per-line auto-submit) in modern terminal emulators -- worth a quick
  rehearsal paste beforehand to confirm your terminal behaves the same way.
"""

from context_demo import LAW_TEXTS, SYSTEM_PREAMBLE, nbytes, read_whole

ALIENS_OUT = f"{LAW_TEXTS}/aliens_act_interactive.txt"
LLC_OUT = f"{LAW_TEXTS}/llc_act_interactive.txt"


def build_aliens_text():
    return [
        ("Aliens Act (full text)", read_whole(f"{LAW_TEXTS}/aliens_act.txt")),
        (
            "Aliens Act -- amendments supplement (whole file)",
            read_whole(f"{LAW_TEXTS}/aliens_act_amendments.txt"),
        ),
    ]


def build_llc_text():
    return [
        (
            "Limited Liability Companies Act (full text)",
            read_whole(f"{LAW_TEXTS}/limited_liability_companies_act.txt"),
        ),
        (
            "Companies Act amendments 2023-2026 supplement (whole file)",
            read_whole(f"{LAW_TEXTS}/companies_act_amendments_2023_2026.txt"),
        ),
    ]


def write_file(out_path, parts):
    body = "\n\n".join(f"===== {label} =====\n{text}" for label, text in parts)
    full = SYSTEM_PREAMBLE + "\n\n" + body
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full)
    print(f"{out_path}: {nbytes(full):,} bytes")


if __name__ == "__main__":
    write_file(ALIENS_OUT, build_aliens_text())
    write_file(LLC_OUT, build_llc_text())
