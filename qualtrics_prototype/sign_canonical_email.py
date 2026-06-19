import argparse
import json
import os
import pcc

# SENSITIVE_COLUMNS = ["QID2_TEXT"]

def rec_bytes(r):
    return json.dumps(r, sort_keys=True).encode()

def ds_bytes(rs):
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rs).encode()

# def sign_rows(sk, rs):
#     out = []
#     for r in rs:
#         h, sig = pcc.sign_data(sk, rec_bytes(r))
#         out.append({"response_id": r["response_id"], "record_hash": h, "record_sig": sig})
#     return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("survey_id")
    parser.add_argument("--base_url", default="https://cmu.yul1.qualtrics.com")
    args = parser.parse_args()
    survey_id = args.survey_id
    out_dir = os.path.join("outputs", survey_id)
    os.makedirs(out_dir, exist_ok=True)

    sk = pcc.load_sk("witness_sk.ed25519")

    records = [json.loads(l) for l in open(os.path.join(out_dir, f"{survey_id}_canonical.jsonl")) if l.strip()]
    row_count = len(records)
    all_cols = sorted({k for r in records for k in r["answers"]})

    # Full dataset receipt
    dh, ds = pcc.sign_data(sk, ds_bytes(records))
    json.dump({"dataset_hash": dh, "dataset_sig": ds, "row_count": row_count, "columns": all_cols},
              open(os.path.join(out_dir, f"{survey_id}_receipt.json"), "w"), indent=2)
    print(f"wrote outputs/{survey_id}/{survey_id}_receipt.json")

    # Per-record receipts
    # json.dump(sign_rows(sk, records), open("email_per_record_receipts.json", "w"), indent=2)
    # print("wrote email_per_record_receipts.json")

    # Redacted dataset receipts
    # redacted = [{"response_id": r["response_id"],
    #              "answers": {k: v for k, v in r["answers"].items() if k not in SENSITIVE_COLUMNS}}
    #             for r in records]
    # retained = [c for c in all_cols if c not in SENSITIVE_COLUMNS]

    # with open("canonical_email_redacted.jsonl", "w") as f:
    #     f.writelines(json.dumps(r, sort_keys=True) + "\n" for r in redacted)

    # rh, rs = pcc.sign_data(sk, ds_bytes(redacted))
    # json.dump({"dataset_hash": rh, "dataset_sig": rs, "row_count": row_count,
    #            "redacted_columns": sorted(SENSITIVE_COLUMNS), "retained_columns": retained},
    #           open("email_redacted_dataset_receipt.json", "w"), indent=2)
    # json.dump(sign_rows(sk, redacted), open("email_redacted_per_record_receipts.json", "w"), indent=2)
    # print("wrote email_redacted_dataset_receipt.json, email_redacted_per_record_receipts.json, canonical_email_redacted.jsonl")

if __name__ == "__main__":
    main()
