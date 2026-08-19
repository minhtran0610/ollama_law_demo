#!/usr/bin/env python3
"""Download a Finlex statute translation PDF and extract its text."""
import argparse
import tempfile

import pymupdf
import requests


def extract(pdf_url, output):
    print(f"Downloading PDF from {pdf_url}...")
    r = requests.get(pdf_url, timeout=45)
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
        pdf_file.write(r.content)
        pdf_file.flush()

        doc = pymupdf.open(pdf_file.name)
        text_content = "\n\n".join(f"{'=' * 70}\n\n{page.get_text()}" for page in doc)
        doc.close()

    with open(output, "w", encoding="utf-8") as f:
        f.write(text_content)

    print(f"Extraction complete. Output written to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_url", help="URL of the Finlex statute translation PDF")
    parser.add_argument("output", help="Path to write the extracted text to")
    args = parser.parse_args()

    extract(args.pdf_url, args.output)
