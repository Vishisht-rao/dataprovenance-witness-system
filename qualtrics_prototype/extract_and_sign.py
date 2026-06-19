import argparse
import subprocess
import sys

DEFAULT_BASE_URL = "https://cmu.yul1.qualtrics.com"

def run(script, survey_id, base_url):
    subprocess.run(
        [sys.executable, script, survey_id, "--base_url", base_url],
        check=True
    )

def main():
    parser = argparse.ArgumentParser(description="Ingest, canonicalize, and sign a Qualtrics survey.")
    parser.add_argument("survey_id", help="Qualtrics survey ID (e.g. SV_4Zx4XItBfyL33jo)")
    parser.add_argument("--base_url", default=DEFAULT_BASE_URL, help="Qualtrics base URL")
    args = parser.parse_args()

    print(f"=== Step 1: Ingest emails for {args.survey_id} ===")
    run("gmail_ingestor.py", args.survey_id, args.base_url)

    print(f"\n=== Step 2: Canonicalize ===")
    run("email_to_canonical_format.py", args.survey_id, args.base_url)

    print(f"\n=== Step 3: Sign ===")
    run("sign_canonical_email.py", args.survey_id, args.base_url)

    print(f"\nDone. Output files in outputs/{args.survey_id}/: {args.survey_id}_srr.jsonl, {args.survey_id}_canonical.jsonl, {args.survey_id}_receipt.json")

if __name__ == "__main__":
    main()
