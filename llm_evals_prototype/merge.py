"""
Merge several signed records (singles and/or batches) into ONE unified record
with a single new signature over all of their LLM requests.

    python merge.py --records r1.json r2.json ... --receipts rc1.json rc2.json ... \
                    --out merged_outputs [--json]

Both lists are pooled and each file is classified by content (a receipt has a
`signature`; everything else is a record), so it does not matter which flag a
file is passed under. Each record is paired with its receipt by cryptographic
identity (the record's recomputed root hash must equal the receipt's
hash/batch_hash) and that receipt's signature is verified against the public key.

The merged record keeps each source record WHOLE, as a value in a `records` map
indexed by its batch_name (falling back to batch_id, or a single record's id).
So nothing is lost — batch_name, model_default, failed_items, every item — and a
researcher can use it directly for post-processing.

The merged_hash is computed the SAME way a batch_hash is: sha256 over every item
across all sources (NOT by hashing the sources' hashes). One new Ed25519
signature is made over it. Because verify.py uses the identical construction, it
checks the merged record with no special math.

Safety: if ANY record has no matching receipt, any signature fails to verify, or
any item's stored hash does not match its recomputed hash, the whole merge is
REFUSED and nothing is written — unverified data is never bound into a new
signature.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pcc
from verify import (all_items, detect_mode, item_files, reconstruct_item_hash,
                    reconstruct_root_hash)


class MergeError(Exception):
    """Raised to refuse a merge; the message is shown to the user verbatim."""


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        raise MergeError(f"could not read {os.path.basename(path)}: {e}")


def _check_item_integrity(record, label):
    """Confirm every item's stored hash matches its recomputed hash."""
    for it in all_items(record):
        cid = it.get("custom_id", it.get("id", "?"))
        if "hash" in it and it["hash"] != reconstruct_item_hash(it):
            raise MergeError(f"{label}: item '{cid}' has been tampered "
                             f"(stored hash != recomputed hash)")


def _source_key(record, used):
    """Pick the map key: batch_name if present, else batch_id / merged_id / id.
    Append a numeric suffix on collision so a source is never silently overwritten."""
    mode = detect_mode(record)
    if mode == "batch":
        base = (record.get("batch_name") or "").strip() or record.get("batch_id") or "batch"
    elif mode == "merged":
        base = record.get("merged_id") or "merged"
    else:
        base = record.get("id") or "record"
    key, i = base, 2
    while key in used:
        key = f"{base}_{i}"
        i += 1
    return key


def merge(record_paths, receipt_paths, out_dir, pk=None, sk=None):
    """Verify all pairs, then keep each whole under `records` and re-sign. Returns a summary."""
    pk = pk or pcc.load_pk("keys/witness_pk.ed25519")

    # Pool every input and classify by content (forgiving of which flag was used).
    pool = [(p, _load(p)) for p in (record_paths or []) + (receipt_paths or [])]
    receipts, records = [], []
    for path, obj in pool:
        (receipts if "signature" in obj else records).append((path, obj))

    if not records:
        raise MergeError("no record files supplied (a record has `items` or `output`, not a `signature`)")

    receipts_by_hash = {}
    for path, rc in receipts:
        h = rc.get("batch_hash") or rc.get("hash") or rc.get("merged_hash")
        if not h:
            raise MergeError(f"{os.path.basename(path)}: receipt has no hash/batch_hash field")
        receipts_by_hash[h] = (path, rc)

    verified, seen = [], set()
    for path, record in records:
        label = os.path.basename(path)
        try:
            root_hash = reconstruct_root_hash(record)
        except Exception as e:
            raise MergeError(f"{label}: not a valid record ({e})")

        _check_item_integrity(record, label)

        if root_hash not in receipts_by_hash:
            raise MergeError(f"{label}: no matching receipt found "
                             f"(its recomputed hash {root_hash[:12]}… matches no uploaded receipt)")
        rc_path, rc = receipts_by_hash[root_hash]
        if not pcc.verify_hexhash(pk, root_hash, rc.get("signature", "")):
            raise MergeError(f"{label} + {os.path.basename(rc_path)}: signature does NOT verify "
                             f"(tampered, or signed by a different key) — merge refused")

        if root_hash in seen:
            continue  # identical source uploaded twice; bind it once
        seen.add(root_hash)
        verified.append(record)

    if not verified:
        raise MergeError("nothing to merge (no verified records)")

    records_map, used = {}, set()
    for record in verified:
        key = _source_key(record, used)
        used.add(key)
        records_map[key] = record

    merged_record = {
        "merged_id": "",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_count": len(records_map),
        "records": records_map,
        "merged_hash": "",
    }
    # merged_hash is computed over every item, exactly like a batch_hash
    # (reconstruct_root_hash ignores the placeholder and recomputes from content).
    merged_hash = reconstruct_root_hash(merged_record)
    merged_record["merged_hash"] = merged_hash
    merged_record["merged_id"] = merged_hash[:8]

    sk = sk or pcc.load_sk("keys/witness_sk.ed25519")
    signature = pcc.sign_hexhash(sk, merged_hash)
    merged_receipt = {"merged_id": merged_hash[:8], "merged_hash": merged_hash, "signature": signature}

    dest = os.path.join(out_dir, f"merged_{merged_hash[:8]}")
    os.makedirs(dest, exist_ok=True)
    record_path = os.path.join(dest, "merged_record.json")
    receipt_path = os.path.join(dest, "merged_receipt.json")
    with open(record_path, "w") as f:
        json.dump(merged_record, f, indent=2)
    with open(receipt_path, "w") as f:
        json.dump(merged_receipt, f, indent=2)

    return {
        "merged_id": merged_hash[:8],
        "item_count": len(all_items(merged_record)),
        "source_count": len(records_map),
        "out_dir": dest,
        "record_path": record_path,
        "receipt_path": receipt_path,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Merge signed records/batches into one unified record + signature."
    )
    parser.add_argument("--records", nargs="*", default=[], metavar="FILE",
                        help="Record JSON files (single records and/or batch_record.json)")
    parser.add_argument("--receipts", nargs="*", default=[], metavar="FILE",
                        help="Receipt JSON files matching the records")
    parser.add_argument("--out", default="merged_outputs",
                        help="Output directory (default: merged_outputs)")
    parser.add_argument("--json", action="store_true",
                        help="Print a machine-readable summary on success")
    args = parser.parse_args()

    try:
        summary = merge(args.records, args.receipts, args.out)
    except MergeError as e:
        print(f"MERGE REFUSED — {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"MERGE FAILED — {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(summary))
    else:
        print(f"Merged {summary['source_count']} source(s) -> {summary['item_count']} item(s)")
        print(f"merged_id: {summary['merged_id']}")
        print(f"wrote: {summary['record_path']}")
        print(f"       {summary['receipt_path']}")


if __name__ == "__main__":
    main()
