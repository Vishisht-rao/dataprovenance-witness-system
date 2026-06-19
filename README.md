# Data Provenance Witness System

Two small, independent **cryptographic witnesses** for research data, built
around the same idea: an output a researcher reports (a survey response, an
LLM call) is hashed and signed by a party other than the researcher, at the
moment the data exists, so anyone can later check that the published data
matches exactly what was witnessed — without re-running the original study.

| Component | Witnesses | Architecture |
|---|---|---|
| [`qualtrics_prototype/`](qualtrics_prototype/) | Qualtrics survey responses | **Pull witness** — fetches each response's official report page directly from Qualtrics over email-triggered polling. |
| [`llm_evals_prototype/`](llm_evals_prototype/) | LLM API calls (via OpenRouter) | **Proxy witness** — brokers the API call itself, so the researcher's API key is never stored and the response can't be edited before signing. |

The two use the same architecture for the crypto itself; only how each one
gets data from its source differs, because the two data sources have
different trust problems (Qualtrics has no independently-fetchable export a
researcher can't pre-edit; OpenRouter has no concept of a witness at all, so
one has to sit in the middle of the call).

## The cryptography, in plain terms

Every witnessed dataset goes through the same two steps:

1. **Hash (SHA-256):** a fingerprint of the exact bytes of the data. Change
   even one character anywhere and the fingerprint comes out completely
   different — there's no way to predict a different input that produces
   the same fingerprint.
2. **Sign (Ed25519):** the witness has a secret key and a public key. The
   secret key signs the fingerprint; anyone holding the public key can
   check that signature, but only the secret key can produce one. The
   public key is shareable; only the secret key must stay private.

So `SUCCESS` on a verification means: *the published bytes are exactly the
bytes the witness's secret key signed* — nothing has been added, removed,
edited, or reordered since. This gives three properties:

- **Data integrity** — changing even one character, or adding/removing a
  row, changes the hash, so the old signature no longer verifies.
- **Unforgeability** — no one can produce a signature that verifies under
  the witness's public key without the witness's secret key. A researcher
  cannot fabricate data and mint a matching signature themselves.
- **Public verifiability** — the signing/verifying procedure is fully
  public; only the secret key is secret. Anyone with the public key and the
  published artifacts can verify offline, with no access to the witness.

Both components implement this with the same small module, `pcc.py`
(present, identically, in each folder).

## The three roles (same shape in both components)

- **Researcher** — runs the study/queries. Never holds the secret key.
- **Witness admin** — runs the witness code, holds the secret key, signs.
  Ideally a different party than the researcher, so the signature means
  something beyond self-attestation.
- **Verifier** — anyone with the public key and the published data. Can
  check authenticity with zero special access.

See each component's own README for the exact commands for each role.

## Pilot data included

Both components ship with real, already-witnessed pilot runs so you can
verify them immediately with no setup:
- `qualtrics_prototype/outputs/` — two real Qualtrics surveys.
- `llm_evals_prototype/tests/test_0/` — a 50-paper batch of LLM review
  requests, plus a merged bundle.

## What this system proves, and what it doesn't

It proves **tamper-evidence after the fact**: once data is witnessed and
signed, no one — including the original researcher — can alter it without
detection. It does **not** prove the underlying data is truthful, complete,
or high quality; a witness can only attest to what it actually saw, not to
what it didn't.

## Repository layout

```
dataprovenance-witness-system/
├── qualtrics_prototype/      survey-response witness
└── llm_evals_prototype/      LLM-API-call witness
```
