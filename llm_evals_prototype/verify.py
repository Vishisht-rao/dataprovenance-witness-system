"""
Verify a published LLM provenance record against its signed receipt.

SINGLE record:
    python verify.py <record_file.json> <receipt_file.json> [--files f1 f2 ...]

BATCH record (one signature over the whole batch):
    python verify.py --batch <batch_record.json> <batch_receipt.json> [--files f1 f2 ...]

MERGED record (one signature over many records/batches kept whole):
    python verify.py --merged <merged_record.json> <merged_receipt.json> [--files f1 f2 ...]

The mode is auto-detected from the record shape when no flag is given, so in
practice you can always just run:
    python verify.py <record> <receipt> [--files ...]

Add --json to print a machine-readable result (used by verification_ui.py) and
exit 0 regardless of outcome; without it, human-readable lines are printed and
the exit code is nonzero on any failure.

Two levels of verification (all modes):

  Level 1 — Signature (always runs):
    Recomputes the hash(es) from the record fields and verifies the Ed25519
    signature in the receipt. Proves the record was not tampered with after it
    was signed by the server. file_hash values stored in attachments are part of
    the signed hash, so editing a file_hash (to cover up a file swap) breaks the
    signature — the researcher cannot re-sign without the private key.

    A batch recomputes each item's hash, then batch_hash = sha256(join of item
    hashes) and verifies the ONE batch signature against it. A merged record
    keeps each source record whole under `records` (indexed by batch_name or
    batch_id); its merged_hash is computed the SAME way a batch_hash is — over
    every item across all sources, not by hashing the sources' hashes — and the
    ONE merged signature is verified against it. So any edit, addition, or
    removal of an item breaks verification.

  Level 2 — File content (only when --files is provided):
    Hashes each supplied file and checks it against the file_hash values across
    every item in the record (recursing into a merged record's sources). Catches
    the case where the file_hash is unchanged but a different physical file is
    shown.

The public key is loaded internally from keys/witness_pk.ed25519.
"""

import argparse
import hashlib
import json
import os
import sys

import pcc


def item_files(item: dict) -> list:
    """The item's attached-file metadata. New records use `files`; older records
    used `attachments` — accept either so both still verify."""
    return item.get("files") or item.get("attachments") or []


def reconstruct_item_hash(item: dict) -> str:
    """Recompute the canonical per-item hash: timestamp|model|prompt|output[|sorted file_hashes].

    `prompt` is the raw user prompt; attached files contribute only their sorted
    content hashes (their text is never part of the record). Older records stored
    the effective prompt under `input` instead — fall back to it so they too verify.
    """
    prompt = item.get("prompt", item.get("input", ""))
    hash_input = f"{item['timestamp']}|{item['model']}|{prompt}|{item['output']}"
    files = item_files(item)
    if files:
        stored_file_hashes = sorted(a["file_hash"] for a in files)
        hash_input += "|" + "|".join(stored_file_hashes)
    return pcc.sha256_bytes(hash_input.encode("utf-8"))


def detect_mode(record: dict) -> str:
    """Infer the record type from its shape.

    A merged record holds whole source records under `records` + a `merged_hash`.
    A batch record carries `items` + `batch_hash`. Anything else is a single
    record file.
    """
    if isinstance(record.get("records"), dict) and "merged_hash" in record:
        return "merged"
    if "items" in record and "batch_hash" in record:
        return "batch"
    return "single"


def all_items(record: dict) -> list:
    """Every LLM request a record contains, in a deterministic order.

    Single -> the record itself. Batch -> its items in stored order. Merged ->
    its sources flattened, with the sources ordered by their item-hash content
    (NOT by their map key), so the order is independent of how the `records` map
    happens to be keyed or serialized — a researcher can re-save the file or
    rename a source key without changing what gets hashed.
    """
    mode = detect_mode(record)
    if mode == "single":
        return [record]
    if mode == "batch":
        return list(record.get("items", []))
    subs = list(record["records"].values())
    subs.sort(key=lambda s: [reconstruct_item_hash(it) for it in all_items(s)])
    out = []
    for s in subs:
        out.extend(all_items(s))
    return out


def reconstruct_root_hash(record: dict) -> str:
    """The hash the receipt's signature is expected to cover, recomputed from content.

    Single -> the item hash. Batch and merged -> sha256(join of every item hash),
    i.e. exactly the batch_hash construction applied to all items the record
    contains. Shared with merge.py so a freshly built record hashes the same way
    it verifies.
    """
    if detect_mode(record) == "single":
        return reconstruct_item_hash(record)
    item_hashes = [reconstruct_item_hash(it) for it in all_items(record)]
    return pcc.sha256_bytes("|".join(item_hashes).encode("utf-8"))


def collect_file_hashes(record: dict) -> dict:
    """{file_hash: filename} across every item in the record (recursing merged)."""
    recorded = {}
    for it in all_items(record):
        for a in item_files(it):
            recorded[a["file_hash"]] = a["filename"]
    return recorded


def compute_file_stats(file_paths, recorded_hashes):
    """Hash each supplied file and compare against recorded_hashes ({hex: filename}).

    Returns (stats, details) where stats summarizes the Level-2 outcome and
    details is a list of (status, message) tuples for human-readable printing.
    """
    matched_hashes = set()
    mismatched = []
    details = []
    for path in file_paths or []:
        basename = os.path.basename(path)
        try:
            with open(path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            mismatched.append(basename)
            details.append(("FAILURE", f"could not read {path}: {e}"))
            continue
        computed = hashlib.sha256(file_bytes).hexdigest()
        if computed in recorded_hashes:
            matched_hashes.add(computed)
            details.append(("SUCCESS", f"{basename} matches recorded hash "
                                       f"(originally: {recorded_hashes[computed]})"))
        else:
            mismatched.append(basename)
            details.append(("FAILURE", f"{basename} does NOT match any file hash in the record"))

    recorded_total = len(recorded_hashes)
    matched = len(matched_hashes)
    stats = {
        "recorded_total": recorded_total,
        "provided": len(file_paths or []),
        "matched": matched,
        "mismatched": mismatched,
        "missing": recorded_total - matched,
    }
    return stats, details


def classify_level2(stats: dict) -> str:
    """na (no files in record) / none (none uploaded) / complete / partial."""
    if stats["recorded_total"] == 0:
        return "na"
    if stats["provided"] == 0:
        return "none"
    if stats["matched"] == stats["recorded_total"] and not stats["mismatched"]:
        return "complete"
    return "partial"


def _finish_files(recorded, files, level1_ok, verbose):
    """Run Level 2 (if files given) and assemble the shared files/level2/ok fields."""
    stats, details = compute_file_stats(files, recorded)
    if files:
        if not recorded:
            if verbose:
                print("[File check] WARNING — record has no files; --files arguments were ignored")
        elif verbose:
            for status, msg in details:
                print(f"[File check] {status} — {msg}")
    level2 = classify_level2(stats)
    ok = level1_ok and not stats["mismatched"]
    return stats, level2, ok


def verify_single(record, receipt, pk, files, verbose=True) -> dict:
    record_id = record.get("id", receipt.get("record_id", "?"))

    hash_hex = reconstruct_item_hash(record)
    level1_ok = pcc.verify_hexhash(pk, hash_hex, receipt.get("signature", ""))
    if verbose:
        print(f"[Signature]  {'SUCCESS' if level1_ok else 'FAILURE'} — record {record_id}")

    recorded = {a["file_hash"]: a["filename"] for a in item_files(record)}
    stats, level2, ok = _finish_files(recorded, files, level1_ok, verbose)

    return {
        "mode": "single",
        "level1_ok": level1_ok,
        "level1_detail": f"record {record_id} signature {'valid' if level1_ok else 'INVALID'}",
        "files": stats,
        "level2": level2,
        "ok": ok,
    }


def _check_items(items, verbose):
    """Per-item integrity over a list of items; returns True if all match."""
    ok = True
    for it in items:
        cid = it.get("custom_id", it.get("id", "?"))
        if it.get("hash") == reconstruct_item_hash(it):
            if verbose:
                print(f"[Item {cid}] integrity SUCCESS")
        else:
            ok = False
            if verbose:
                print(f"[Item {cid}] integrity FAILURE — recomputed hash != stored hash")
    return ok


def verify_batch(record, receipt, pk, files, verbose=True) -> dict:
    ident = record.get("batch_id", receipt.get("batch_id", "?"))
    items = record.get("items", [])
    level1_ok = True

    if not items:
        if verbose:
            print("[Batch] FAILURE — record has no items")
        return {"mode": "batch", "level1_ok": False,
                "level1_detail": f"batch {ident} has no items",
                "files": {"recorded_total": 0, "provided": len(files or []),
                          "matched": 0, "mismatched": [], "missing": 0},
                "level2": "na", "ok": False}

    if not _check_items(items, verbose):  # Level 1a: per-item integrity
        level1_ok = False

    # Level 1b: recompute batch_hash from the item hashes (stored order).
    batch_hash = reconstruct_root_hash(record)
    if record.get("batch_hash") and record["batch_hash"] != batch_hash:
        level1_ok = False
        if verbose:
            print("[Signature] FAILURE — recomputed hash != stored batch_hash "
                  "(items edited, added, removed, or reordered)")

    # Level 1c: the single batch signature is the cryptographic ground truth.
    if not pcc.verify_hexhash(pk, batch_hash, receipt.get("signature", "")):
        level1_ok = False

    if verbose:
        print(f"[Batch Signature]  {'SUCCESS' if level1_ok else 'FAILURE'} — "
              f"batch {ident} ({len(items)} signed item(s))")
        failed = record.get("failed_items") or []
        if failed:
            print(f"[Note] {len(failed)} item(s) failed during the run and are NOT covered by the "
                  f"signature (requested {record.get('requested_count', '?')}, "
                  f"signed {record.get('item_count', len(items))}).")

    recorded = collect_file_hashes(record)
    stats, level2, ok = _finish_files(recorded, files, level1_ok, verbose)

    return {
        "mode": "batch",
        "level1_ok": level1_ok,
        "level1_detail": f"batch {ident} signature {'valid' if level1_ok else 'INVALID'} "
                         f"({len(items)} item(s))",
        "files": stats,
        "level2": level2,
        "ok": ok,
    }


def verify_merged(record, receipt, pk, files, verbose=True) -> dict:
    ident = record.get("merged_id", "?")
    recs = record.get("records") or {}
    level1_ok = True

    if not recs:
        if verbose:
            print("[Merged] FAILURE — record has no sources")
        return {"mode": "merged", "level1_ok": False,
                "level1_detail": f"merged {ident} has no sources",
                "files": {"recorded_total": 0, "provided": len(files or []),
                          "matched": 0, "mismatched": [], "missing": 0},
                "level2": "na", "ok": False}

    # Level 1a: each source kept whole — recompute its own root hash from content
    # and check it against the hash that source stores (pinpoints a tampered one).
    for key, sub in recs.items():
        smode = detect_mode(sub)
        rh = reconstruct_root_hash(sub)
        stored = (sub.get("merged_hash") if smode == "merged"
                  else sub.get("batch_hash") if smode == "batch"
                  else sub.get("hash"))
        src_ok = stored is None or stored == rh
        if not src_ok:
            level1_ok = False
        if verbose:
            print(f"[Source {key}] integrity {'SUCCESS' if src_ok else 'FAILURE'} "
                  f"({smode}, {len(all_items(sub))} item(s))")

    # Level 1b: recompute merged_hash over every item (like a batch_hash).
    merged_hash = reconstruct_root_hash(record)
    if record.get("merged_hash") and record["merged_hash"] != merged_hash:
        level1_ok = False
        if verbose:
            print("[Signature] FAILURE — recomputed merged_hash != stored merged_hash "
                  "(an item was edited, added, or removed)")

    # Level 1c: the single merged signature is the cryptographic ground truth.
    if not pcc.verify_hexhash(pk, merged_hash, receipt.get("signature", "")):
        level1_ok = False

    items = all_items(record)
    if verbose:
        print(f"[Merged Signature]  {'SUCCESS' if level1_ok else 'FAILURE'} — "
              f"merged {ident} ({len(recs)} source(s), {len(items)} item(s))")

    recorded = collect_file_hashes(record)
    stats, level2, ok = _finish_files(recorded, files, level1_ok, verbose)

    return {
        "mode": "merged",
        "level1_ok": level1_ok,
        "level1_detail": f"merged {ident} signature {'valid' if level1_ok else 'INVALID'} "
                         f"({len(recs)} source(s), {len(items)} item(s))",
        "files": stats,
        "level2": level2,
        "ok": ok,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify an LLM provenance record (single, batch, or merged) and its signed receipt."
    )
    parser.add_argument("record_file",  help="Path to the published record JSON")
    parser.add_argument("receipt_file", help="Path to the published receipt JSON")
    parser.add_argument("--batch", action="store_true",
                        help="Force batch mode (one signature over all items)")
    parser.add_argument("--merged", action="store_true",
                        help="Force merged mode (one signature over many whole sources)")
    parser.add_argument("--json", action="store_true",
                        help="Print a machine-readable result and exit 0 regardless of outcome")
    parser.add_argument(
        "--files", nargs="+", metavar="FILE",
        help="Original attached files (optional). When provided, their SHA-256 "
             "hashes are checked against the file_hash values in the record."
    )
    args = parser.parse_args()

    try:
        with open(args.record_file) as f:
            record = json.load(f)
    except Exception as e:
        _fail(args.json, f"could not read record file: {e}")

    try:
        with open(args.receipt_file) as f:
            receipt = json.load(f)
    except Exception as e:
        _fail(args.json, f"could not read receipt file: {e}")

    try:
        pk = pcc.load_pk("keys/witness_pk.ed25519")
    except Exception as e:
        _fail(args.json, f"could not load public key: {e}")

    verbose = not args.json
    mode = detect_mode(record)
    if args.merged or mode == "merged":
        result = verify_merged(record, receipt, pk, args.files, verbose=verbose)
    elif args.batch or mode == "batch":
        result = verify_batch(record, receipt, pk, args.files, verbose=verbose)
    else:
        result = verify_single(record, receipt, pk, args.files, verbose=verbose)

    if args.json:
        print(json.dumps(result))
        sys.exit(0)
    if not result["ok"]:
        sys.exit(1)


def _fail(as_json, message):
    if as_json:
        print(json.dumps({"mode": "unknown", "level1_ok": False, "level1_detail": message,
                          "files": {"recorded_total": 0, "provided": 0, "matched": 0,
                                    "mismatched": [], "missing": 0},
                          "level2": "na", "ok": False}))
        sys.exit(0)
    print(f"FAILURE — {message}")
    sys.exit(1)


if __name__ == "__main__":
    main()
