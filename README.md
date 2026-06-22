# Data Provenance Witness System

Two cryptographic witnesses for research data. Each one hashes and signs a data
record at the moment it is created, by a party other than the researcher, so
the published data can later be checked against what was witnessed. If even
one record was added, removed, or changed after the fact, the check fails.

| Component | Witnesses | Architecture |
|---|---|---|
| [`qualtrics_prototype/`](qualtrics_prototype/) | Qualtrics survey responses | **Pull witness.** Fetches each response's official report page directly from Qualtrics, using polling triggered by email. |
| [`llm_evals_prototype/`](llm_evals_prototype/) | LLM API calls (via OpenRouter) | **Proxy witness.** Brokers the API call itself, so the researcher's API key is never stored and the response cannot be edited before signing. |

Both use the same architecture for the crypto itself. Only how each one gets
data from its source differs, because the two data sources have different
trust problems. Qualtrics has no export that can be independently fetched and
that a researcher cannot edit beforehand. OpenRouter has no concept of a
witness at all, so one has to sit in the middle of the call.

## The cryptography, in plain terms

Every witnessed dataset goes through the same two steps.

1. **Hash (SHA-256):** a fingerprint of the exact bytes of the data. Change
   even one character anywhere and the fingerprint comes out completely
   different. There is no way to predict a different input that produces
   the same fingerprint.
2. **Sign (Ed25519):** the witness has a secret key and a public key. The
   secret key signs the fingerprint. Anyone holding the public key can
   check that signature, but only the secret key can produce one. The
   public key is shareable. Only the secret key must stay private.

So `SUCCESS` on a verification means the published bytes are exactly the
bytes the witness's secret key signed. Nothing has been added, removed,
edited, or reordered since. This gives three properties:

* **Data integrity:** changing even one character, or adding or removing a
  row, changes the hash, so the old signature no longer verifies.
* **Unforgeability:** no one can produce a signature that verifies under
  the witness's public key without the witness's secret key. A researcher
  cannot fabricate data and mint a matching signature themselves.
* **Public verifiability:** the signing and verifying procedure is fully
  public. Only the secret key is secret. Anyone with the public key and the
  published artifacts can verify offline, with no access to the witness.

Both components implement this with the same small module, `pcc.py`
(present, identically, in each folder).

## The three roles (same shape in both components)

* **Researcher:** runs the study or queries. Never holds the secret key.
* **Witness admin:** runs the witness code, holds the secret key, signs.
  Ideally a different party than the researcher, so the signature means
  something beyond attestation from the researcher themselves.
* **Verifier:** anyone with the public key and the published data. Can
  check authenticity with zero special access.

See each component's own README for the exact commands for each role.

## Running the UIs

There are three separate apps. Each needs its dependencies installed first
(`pip install -r requirements.txt` inside that component's folder), and each
must be run from inside its own folder.

**1. LLM Evals query UI** (the researcher facing tool that actually calls
OpenRouter and produces signed records):
```
cd llm_evals_prototype
uvicorn main:app --reload
```
Open **http://localhost:8000**.

**2. LLM Evals verification UI** (point and click Verify / Merge Receipts
for `llm_evals_prototype` records):
```
cd llm_evals_prototype
python3 verification_ui.py
```
Open **http://localhost:8053**.

**3. Qualtrics verification UI** (point and click verifier for
`qualtrics_prototype` datasets):
```
cd qualtrics_prototype
python3 verification_ui.py
```
Open **http://localhost:8052**.

> **App 2 (LLM Evals verification UI) uses port 8053, the same port as the
> [tutorial walkthrough UI](#walkthrough-tutorials) below.** Don't run both
> at the same time unless you change one of their ports. Apps 1 (8000) and
> 3 (8052) don't conflict with anything.

## Walkthrough tutorials

Step by step, screenshot heavy walkthroughs for every workflow in both
components live in [`tutorials/`](tutorials/): Qualtrics setup, Qualtrics
verification, LLM provenance (single prompt and batch processing), and LLM
verification (merging and verifying). Run them interactively:

```
python3 tutorials/tutorial_ui.py    # http://localhost:8053
```

or, if you'd rather just read one, open the matching PDF under
[`tutorials/pdfs/`](tutorials/pdfs/).

## Pilot data included

Both components ship with real, already witnessed pilot runs so you can
verify them immediately with no setup.

* `qualtrics_prototype/outputs/`: two real Qualtrics surveys.
* `llm_evals_prototype/tests/test_0/`: a batch of 50 LLM review requests,
  plus a merged bundle.

## What this system proves, and what it doesn't

It proves tamper evidence after the fact. Once data is witnessed and signed,
no one, including the original researcher, can alter it without detection.
It does not prove the underlying data is truthful, complete, or high
quality. A witness can only attest to what it actually saw, not to what it
didn't.

## Repository layout

```
dataprovenance-witness-system/
├── qualtrics_prototype/      survey response witness
├── llm_evals_prototype/      LLM API call witness
└── tutorials/                walkthrough UI + PDFs for both components
```
