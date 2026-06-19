import json, sys, argparse
import pcc

def load_records(path):
    return [json.loads(l) for l in open(path) if l.strip()]

def rec_bytes(r):
    return json.dumps(r, sort_keys=True).encode()

def ds_bytes(rs):
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rs).encode()

def verify_dataset(pk, data_path, receipt_path):
    records = load_records(data_path)
    receipt = json.load(open(receipt_path))
    ok = pcc.verify_data(pk, ds_bytes(records), receipt["dataset_sig"])
    print(f"{'SUCCESS' if ok else 'FAILURE'} — dataset ({receipt_path}): {len(records)} rows")
    if not ok:
        sys.exit(1)

def verify_row(pk, response_id, data_path, receipts_path):
    records = {r["response_id"]: r for r in load_records(data_path)}
    if response_id not in records:
        print(f"FAILURE — {response_id} not found in {data_path}")
        sys.exit(1)
    receipts = {e["response_id"]: e for e in json.load(open(receipts_path))}
    if response_id not in receipts:
        print(f"FAILURE — {response_id} not found in {receipts_path}")
        sys.exit(1)
    ok = pcc.verify_data(pk, rec_bytes(records[response_id]), receipts[response_id]["record_sig"])
    print(f"{'SUCCESS' if ok else 'FAILURE'} — row {response_id} ({receipts_path})")
    if not ok:
        sys.exit(1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True, help="Path to canonical JSONL dataset")
    p.add_argument("--receipt", required=True, help="Path to receipt JSON")

    args = p.parse_args()
    pk = pcc.load_pk("witness_pk.ed25519")
    verify_dataset(pk, args.data, args.receipt)

if __name__ == "__main__":
    main()
