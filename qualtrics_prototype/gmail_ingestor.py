from __future__ import print_function

import os
import os.path
import base64
from email.parser import BytesParser
from email.policy import default

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials

import json
from datetime import datetime, timezone
import re
import requests
from bs4 import BeautifulSoup

import argparse

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def is_authentic_qualtrics(eml):
    # Gmail adds Authentication-Results headers after receiving.
    ar = eml.get("Authentication-Results", "") or ""
    ar_l = ar.lower()
    return ("dkim=pass" in ar_l) and ("dmarc=pass" in ar_l) and ("header.from=qemailserver.com" in ar_l)

def get_service():
    creds = None
    if os.path.exists("token.json"):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def extract_plain_text(eml):
    body = eml.get_body(preferencelist=("plain",))
    if body:
        return body.get_content()
    return ""

def extract_srr_url_from_text(text: str):
    if not text:
        return None
    m = re.search(r"(https://[^\s]+/apps/single-response-reports/reports/[A-Za-z0-9_\-]+)", text)
    return m.group(1) if m else None

def fetch_srr_html(url: str) -> str:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text

def parse_srr_response_id(html: str) -> str:
    m = re.search(r"<title>\s*Response:\s*(R_[A-Za-z0-9]+)\s*</title>", html, re.IGNORECASE)
    return m.group(1) if m else ""

def parse_srr_answers(html: str):
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    for qa in soup.select("div.question-answer[id^='QID']"):
        qid = qa.get("id")  # e.g. QID3
        a_el = qa.select_one(".answer")
        if not qid or not a_el:
            continue

        # text entry vs choice
        is_text = a_el.select_one("p") is not None
        key = f"{qid}_TEXT" if is_text else qid

        a_text = a_el.get_text(" ", strip=True)
        a_text = re.sub(r"\s+", " ", a_text).strip()
        out[key] = a_text

    return {k: out[k] for k in sorted(out.keys())}

def mark_as_read(service, msg_id: str):
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()

def fetch_email(service, msg_id: str):
    full = service.users().messages().get(userId="me", id=msg_id, format="raw").execute()
    raw = base64.urlsafe_b64decode(full["raw"].encode("utf-8"))
    return BytesParser(policy=default).parsebytes(raw)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("survey_id")
    parser.add_argument("--base_url", default="https://cmu.yul1.qualtrics.com")
    args = parser.parse_args()

    service = get_service()
    target_survey_id = args.survey_id
    out_dir = os.path.join("outputs", target_survey_id)
    os.makedirs(out_dir, exist_ok=True)
    q = f'is:unread subject:"{target_survey_id}"'

    res = service.users().messages().list(userId="me", q=q, maxResults=50).execute()
    msgs = res.get("messages", [])

    print(f"Found {len(msgs)} unread matching messages.")
    if not msgs:
        return

    wrote = 0
    rejected = 0
    skipped = 0

    for m in msgs:
        mid = m["id"]
        eml = fetch_email(service, mid)

        if not is_authentic_qualtrics(eml):
            rejected += 1
            # Mark as read anyway so it doesn't block future runs
            mark_as_read(service, mid)
            continue

        text = extract_plain_text(eml)
        srr_url = extract_srr_url_from_text(text)
        if not srr_url:
            skipped += 1
            mark_as_read(service, mid)
            continue

        html = fetch_srr_html(srr_url)
        response_id = parse_srr_response_id(html)
        answers = parse_srr_answers(html)

        if not response_id or not answers:
            skipped += 1
            mark_as_read(service, mid)
            continue

        record = {
            "source": "qualtrics_email_srr",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "srr_url": srr_url,
            "response_id": response_id,
            "answers": answers,
        }

        with open(os.path.join(out_dir, f"{target_survey_id}_srr.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

        wrote += 1
        mark_as_read(service, mid)

    print("wrote:", wrote, "rejected:", rejected, "skipped:", skipped)

if __name__ == "__main__":
    main()
