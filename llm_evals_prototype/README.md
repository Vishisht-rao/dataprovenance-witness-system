# LLM-Evals Witness

A middleware witness that sits between a researcher and the OpenRouter API.
Every (prompt, output) pair the researcher gets back is hashed and signed
before it ever leaves the server, so a published result can be checked
against tampering later — without the witness ever seeing or storing the
researcher's API key.

## The three roles

| Role | Who | What they do |
|---|---|---|
| **Researcher** | wants to run LLM queries | Brings their own OpenRouter API key, types a prompt (or uploads a batch), gets back a signed record + receipt. Never touches the secret key. |
| **Witness admin** | runs this server | Hosts `main.py` and holds `keys/witness_sk.ed25519`. For the guarantee to mean anything beyond "I trust my own laptop," this should ideally be a different party than the researcher — e.g. a shared lab server — though for a quick pilot you can run it on your own machine. |
| **Verifier** | anyone (reviewer, reader) | Needs only `keys/witness_pk.ed25519` + the published record + receipt. Runs `verify.py`. |

## How it works, end to end

1. **Witness admin** starts the server (see Setup below):
   ```
   uvicorn main:app --reload
   ```
   and opens `http://localhost:8000` (or shares that URL/host with the
   researcher, if hosted elsewhere).
2. **Researcher** enters their own OpenRouter API key (never written to
   disk — held only for the duration of the request), picks a model, types
   a prompt, and submits.
3. The server calls OpenRouter on the researcher's behalf, then:
   - captures one UTC timestamp,
   - builds `hash_input = f"{timestamp}|{model}|{prompt}|{output}"` (plus
     any attached files' SHA-256 hashes, sorted, appended — files are bound
     by hash only, their content is never stored in the record),
   - SHA-256 hashes that string,
   - signs the hash with the Ed25519 secret key,
   - writes one record file + one receipt file under `logs/<researcher_id>/`.
4. The researcher gets back the record + receipt and can publish both
   (e.g. alongside their paper).
5. **Verifier** runs:
   ```
   python verify.py record.json receipt.json
   ```
   which recomputes the hash from the record's own fields and checks the
   signature against `keys/witness_pk.ed25519`. `SUCCESS` means: this exact
   (timestamp, model, prompt, output) was witnessed and signed, and nothing
   in it has been edited since.

## Batch mode

OpenRouter has no native batch API, so a batch is just many real-time calls
fired under the hood, bound by **one** signature:

1. Researcher switches "Workflow Mode" to **Batch Processing (JSONL)** and
   uploads a `.jsonl` file (one request per line, only `prompt` required)
   plus any files it references by name — or picks "Same prompt for every
   file" to upload files + one shared prompt and have the JSONL built
   automatically.
2. Each line runs as its own call; transient errors (429/5xx) auto-retry,
   permanent errors are disclosed but excluded from the signature.
3. Once the researcher finalizes, the server computes one hash per
   successful item (same formula as above), joins them in file order, and
   signs `batch_hash = sha256(hash_1|hash_2|...|hash_N)` once.
4. Researcher publishes `batch_record.json` + `batch_receipt.json` — the
   two files together are the whole publishable bundle, nothing else.

Verify with:
```
python verify.py --batch batch_record.json batch_receipt.json
```

## Merging multiple signed batches/records

`merge.py` combines several already-signed records/batches into one new
signed bundle, re-verifying every source's signature first and refusing to
merge if any source fails:
```
python merge.py --records r1.json r2.json --receipts rc1.json rc2.json --out merged_outputs
```
See `tests/test_0/outputs/merged_record.json` / `merged_receipt.json` for a
real example, verifiable with `python verify.py --merged ...`.

## Verifying a file attachment was not swapped

Level 1 (signature only) does not look at file contents, only their stored
hashes. To also check the original files:
```
python verify.py record.json receipt.json --files path/to/original.pdf
```

## Setup (witness admin)

```
pip install -r requirements.txt
python key_generator.py        # writes keys/witness_sk.ed25519 + keys/witness_pk.ed25519
uvicorn main:app --reload
```
`keys/witness_sk.ed25519` must stay on the witness machine only — it is
git-ignored. `keys/witness_pk.ed25519` is meant to be shared (it is what
verifiers use) and is tracked in this repo, already matching the real pilot
data under `tests/`.

A "Run unsigned" mode is allowed if no secret key is present, purely for
local experimentation — published/citable results should always come from a
run where the key exists.

## What's in `tests/`

A real pilot run, `test_0`: 50 arXiv cs.AI papers, one batch of 50
single-prompt review requests (`batch.jsonl`, prompt: "Write a review of
this paper in 2–3 paragraphs", model `openai/gpt-5.4-nano`), with two
finalized signed batches under `outputs/` and one merged bundle combining
them — all directly verifiable with the commands above (Level 1, signature
only). `download_log.txt` lists which papers were used; the original PDFs
themselves are too large for this repo and are hosted at: `[TODO: Drive
link]`. To run the optional Level 2 file-hash check (`--files`), download
them from there first.

## What this does and does not prove

- **Proves:** a specific published output was actually generated by a
  specific published input prompt — this exact (model, prompt, output)
  pair was returned by OpenRouter and signed by the witness at the stated
  timestamp, and the record has not been edited since.
- **Does not prove:** that the model's output is correct, or that the
  published data contains *all* the requests the researcher made — if they
  made many calls, they could selectively omit some from what gets signed
  and published. If the witness admin is the same person as the researcher,
  the guarantee also reduces to "I didn't edit OpenRouter's response after
  the fact" rather than independent third-party witnessing — running the
  server on a machine the researcher does not control strengthens the claim.

## Other tools in this folder
- `verification_ui.py` — a Dash point-and-click verifier:
  ```
  python3 verification_ui.py    # http://localhost:8053
  ```

## Security note
Your OpenRouter API key is never saved to disk. It is used only for the
duration of the request and discarded immediately after.
