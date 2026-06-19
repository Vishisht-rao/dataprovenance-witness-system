"""
Download 50 short arXiv papers (< 20 pages) into pdfs/ and write batch.jsonl.

Usage:
    python download_papers.py

Requires: requests, pypdf  (both available in the llm_evals_prototype venv)
"""

import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pypdf

PDFS_DIR    = Path(__file__).parent / "pdfs"
JSONL_PATH  = Path(__file__).parent / "batch.jsonl"
TARGET      = 50
MAX_PAGES   = 19          # strictly less than 20
BATCH_SIZE  = 80          # papers to fetch per API call
DELAY_API   = 3.0         # seconds between arXiv API calls (their guideline)
DELAY_PDF   = 2.0         # seconds between PDF downloads
PROMPT      = "Write a review of this paper in 2-3 paragraphs."

ARXIV_API   = "https://export.arxiv.org/api/query"
CATEGORIES  = ["cs.AI", "cs.CL", "cs.LG"]  # mix of AI/ML/NLP — many short papers

NS = "{http://www.w3.org/2005/Atom}"


def fetch_ids(category: str, start: int, max_results: int) -> list[dict]:
    url = (
        f"{ARXIV_API}?search_query=cat:{category}"
        f"&start={start}&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        xml = r.read()
    root = ET.fromstring(xml)
    entries = []
    for entry in root.findall(f"{NS}entry"):
        id_url = entry.find(f"{NS}id").text.strip()
        arxiv_id = id_url.split("/abs/")[-1].replace("/", "")
        title = entry.find(f"{NS}title").text.strip().replace("\n", " ")
        entries.append({"id": arxiv_id, "title": title})
    return entries


def count_pages(path: Path) -> int:
    try:
        reader = pypdf.PdfReader(str(path))
        return len(reader.pages)
    except Exception:
        return 999


def main():
    PDFS_DIR.mkdir(exist_ok=True)
    collected: list[dict] = []     # {id, title, filename}
    seen_ids: set[str] = set()

    cat_idx   = 0
    api_start = 0

    print(f"Targeting {TARGET} papers with < {MAX_PAGES + 1} pages …\n")

    while len(collected) < TARGET:
        category = CATEGORIES[cat_idx % len(CATEGORIES)]
        print(f"  Fetching metadata: cat={category} start={api_start} …")
        try:
            entries = fetch_ids(category, api_start, BATCH_SIZE)
        except Exception as e:
            print(f"  API error: {e}. Retrying after 10 s …")
            time.sleep(10)
            continue
        time.sleep(DELAY_API)

        if not entries:
            cat_idx  += 1
            api_start = 0
            continue

        for entry in entries:
            if len(collected) >= TARGET:
                break
            aid = entry["id"]
            if aid in seen_ids:
                continue
            seen_ids.add(aid)

            pdf_url  = f"https://arxiv.org/pdf/{aid}"
            pdf_path = PDFS_DIR / f"{aid}.pdf"

            # skip if already downloaded from a previous run
            if not pdf_path.exists():
                try:
                    print(f"  [{len(collected)+1:>2}/{TARGET}] Downloading {aid} …", end=" ", flush=True)
                    req = urllib.request.Request(
                        pdf_url, headers={"User-Agent": "Mozilla/5.0 (research-test)"}
                    )
                    with urllib.request.urlopen(req, timeout=60) as r:
                        pdf_path.write_bytes(r.read())
                    time.sleep(DELAY_PDF)
                except Exception as e:
                    print(f"SKIP (download error: {e})")
                    continue
            else:
                print(f"  [{len(collected)+1:>2}/{TARGET}] Already have {aid} …", end=" ", flush=True)

            pages = count_pages(pdf_path)
            if pages > MAX_PAGES:
                print(f"SKIP ({pages} pages > {MAX_PAGES})")
                pdf_path.unlink(missing_ok=True)
                continue

            print(f"OK ({pages} pages)")
            collected.append({
                "id":       aid,
                "title":    entry["title"],
                "filename": pdf_path.name,
                "pages":    pages,
            })

        api_start += BATCH_SIZE
        if api_start > 1000:
            cat_idx  += 1
            api_start = 0

    # Write JSONL
    lines = []
    for paper in collected:
        obj = {
            "custom_id": paper["id"],
            "prompt":    PROMPT,
            "files":     [paper["filename"]],
        }
        lines.append(json.dumps(obj))

    JSONL_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nDone. {len(collected)} papers collected.")
    print(f"PDFs : {PDFS_DIR}")
    print(f"JSONL: {JSONL_PATH}")

    # Print a summary table
    print("\n  #   ID                     Pages  Title (truncated)")
    print("  " + "-" * 70)
    for i, p in enumerate(collected, 1):
        print(f"  {i:>2}  {p['id']:<22}  {p['pages']:>4}   {p['title'][:38]}")


if __name__ == "__main__":
    main()
