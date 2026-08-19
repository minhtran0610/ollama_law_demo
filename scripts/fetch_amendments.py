#!/usr/bin/env python3
"""Fetch Aliens Act amendment press releases from Migri and save just the article text."""
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT = str(Path(__file__).resolve().parent.parent / "law_texts" / "aliens_act_amendments.txt")

urls = [
    "https://migri.fi/en/-/amendments-to-aliens-act-on-6-may-specify-the-definition-of-legal-and-illegal-residence-in-finland",
    "https://migri.fi/en/-/amendments-to-aliens-act-on-6-may-new-obligation-to-cooperate-and-changes-to-entry-bans-and-withdrawal-of-residence-permits",
    "https://migri.fi/en/-/amendments-to-the-aliens-act-from-1-june-impacts-on-customers-receiving-international-protection",
    "https://migri.fi/en/-/the-aliens-act-will-change-on-11-june-residence-permits-for-employed-persons-will-be-affected",
    "https://migri.fi/en/-/aliens-act-s-provisions-on-permanent-residence-permit-amended-as-of-8-january-2026",
    "https://migri.fi/en/-/amendments-to-provisions-on-permanent-residence-permits-enter-into-force-on-8-january-2026",
    "https://migri.fi/en/-/aliens-act-amended-on-12-june-2026-affects-removal-from-country-and-entry-ban",
    "https://migri.fi/en/-/aliens-act-amended-on-12-june-2026-affects-beneficiaries-of-temporary-protection",
    "https://migri.fi/en/-/applying-for-international-protection-and-the-processing-of-the-applications-changes-as-of-12-june",
    "https://migri.fi/en/-/changes-in-legislation-affecting-reception-services-as-of-12-june-2026",
    "https://migri.fi/en/-/eu-reforms-its-asylum-system-changes-also-to-reception-services-and-removals-from-the-country-as-of-12-june-2026",
]


def extract_article(html):
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_="journal-content-article")
    if container is None:
        return None

    title = container.find("h1")
    date = container.select_one(".d-inline-block .date")
    time = container.select_one(".d-inline-block .time")
    type_span = container.select_one(".meta .label")
    body = container.find(attrs={"itemprop": "articleBody"})

    lines = []
    if title:
        lines.append(title.get_text(strip=True))
    if date:
        date_line = f"Publication date {date.get_text(strip=True)}"
        if time:
            date_line += f" {time.get_text(strip=True)}"
        lines.append(date_line)
    if type_span:
        lines.append(type_span.get_text(strip=True))
    lines.append("")

    if body:
        for el in body.find_all(["p", "h2", "h3", "li"]):
            if el.name == "li":
                # own text only -- nested <ul><li> sublists are walked separately
                # so include them, not the parent li's get_text (which would repeat them)
                text = " ".join(
                    piece
                    for c in el.contents
                    if getattr(c, "name", None) not in ("ul", "ol")
                    for piece in [c.get_text(" ", strip=True) if hasattr(c, "get_text") else str(c).strip()]
                    if piece
                )
                indent = "  " * len(el.find_parents("li"))
                text = f"{indent}- {text}" if text else None
            else:
                text = el.get_text(" ", strip=True)
            if text:
                lines.append(text)

    return "\n".join(lines)


print("=" * 70)
print("Fetching Aliens Act Amendments")

with open(OUTPUT, "w") as f_out:
    f_out.write("=== Aliens Act Amendments (after 2023) ===\n\n")

    for url in urls:
        print(f"[{url[-50:]}]", end="", flush=True)

        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
        r.raise_for_status()

        article = extract_article(r.text)

        f_out.write(f"{'-' * 50}\n\n")
        if article:
            f_out.write(article + "\n\n")
        else:
            f_out.write(f"[Could not extract article content from {url}]\n\n")
        print(" ok")

print("Done!")
