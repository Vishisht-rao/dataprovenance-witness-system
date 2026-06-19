"""
LLM Provenance Logger — middleware between a researcher and the OpenRouter API.

Single-prompt mode (POST /api/query):
  1. Returns a job_id immediately so the frontend does not have to wait
  2. Runs the LLM call as an asyncio background task
  3. Records the raw prompt, output, model, metadata, and UTC timestamp. Any
     attached files are stored as {filename, file_hash} only (not their text).
  4. Computes a SHA-256 hash of (timestamp|model|prompt|output[|file_hashes])
  5. Signs the hash with an Ed25519 private key (if keys/witness_sk.ed25519 exists)
  6. Writes one JSON record file and one receipt file per request under
     logs/{researcher_id}/

Batch mode (POST /api/batch-query):
  The researcher uploads a JSONL file (one request per line) plus any referenced
  files. Each line is run as its own real-time LLM call (OpenRouter has no native
  batch API), producing a per-item record. The whole batch is then bound by ONE
  signature: batch_hash = sha256(join of all per-item hashes), signed once. The
  results live under logs/{researcher_id}/batch_{batch_id}/.

The researcher receives the record(s) and receipt, which they can publish. Anyone
can then verify authenticity with:
    python verify.py record.json receipt.json                 (single)
    python verify.py --batch batch_record.json batch_receipt.json   (batch)
"""

import asyncio
import base64
import hashlib
import io
import json
import mimetypes
import os
import random
import re
import time
import uuid
import zipfile
from datetime import datetime, timezone
from glob import glob

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

import pcc

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT = 120

# PDFs are sent to the model NATIVELY (as a `file` content part). A model that
# supports native file input (Gemini, Claude, GPT — see input_modalities) reads
# the real document and we send NO plugin, so it goes through the model's own
# (large, ~tens-of-MB) file pipeline. A model WITHOUT native file support can't
# read a PDF, so OpenRouter must parse it for us — we pin the FREE "cloudflare-ai"
# engine (PDF→markdown) so those models never hit the paid "mistral-ocr" default.
# IMPORTANT: specifying ANY engine overrides native, so we attach the plugin
# ONLY for non-native models. (cloudflare-ai has a lower size ceiling than native,
# which is why forcing it on every model made large PDFs fail with "Failed to parse".)
PDF_PARSER_ENGINE = "cloudflare-ai"

# Client errors that mean "this model/parser could not take the PDF as sent"
# (too large, unparseable, context too long). On any of these for a PDF item we
# retry that item once with local pypdf text extraction so it still completes.
PDF_FALLBACK_STATUS = {400, 413, 415, 422}

# OpenRouter model metadata is fetched once and cached to learn which models
# accept files natively (architecture.input_modalities contains "file").
_NATIVE_MODELS_TTL = 3600  # seconds
_native_models_cache: dict = {"ts": 0.0, "ids": None}

# Batch tuning
BATCH_CONCURRENCY = 5          # max simultaneous in-flight calls in a batch
MAX_ATTEMPTS = 3               # total attempts per item for transient failures
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
FATAL_STATUS = {401, 402, 403}  # bad key / no credits — almost certainly global

# In-memory job store: {job_id -> job_dict}
# Jobs survive as long as the server process is running.
_jobs: dict = {}

# Load signing key once at startup (optional — runs unsigned if key is absent)
_sk = None
try:
    _sk = pcc.load_sk("keys/witness_sk.ed25519")
except Exception:
    pass

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


# ── Models ──────────────────────────────────────────────────────────────────
class FileAttachment(BaseModel):
    filename: str
    mime_type: str
    data_b64: str  # raw base64, no data-URL prefix


class QueryRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    api_key: str
    researcher_id: str
    model: str
    model_params: dict = {}
    prompt: str
    files: list[FileAttachment] = []


class ItemError(Exception):
    """A single LLM call failed. Carries enough info to classify and display it."""

    def __init__(self, http_status, message, retryable=False, fatal=False, retry_after=None):
        self.http_status = http_status      # int or None (network/our-side errors)
        self.message = message
        self.retryable = retryable          # transient → safe to retry
        self.fatal = fatal                  # global (auth/billing) → abort the batch
        self.retry_after = retry_after      # seconds, parsed from Retry-After header
        super().__init__(message)


# ── Helpers shared by single + batch ──────────────────────────────────────────
def _extract_pdf_text(data: bytes) -> str:
    """Local text-layer extraction — the fallback when native PDF upload fails."""
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(data))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    # pypdf can emit surrogate code points from malformed fonts; strip them so
    # JSON serialisation never hits a UnicodeEncodeError.
    return text.encode("utf-8", errors="replace").decode("utf-8")


def _has_pdf(files: list[FileAttachment]) -> bool:
    return any(f.mime_type.lower() == "application/pdf" for f in files)


def _build_messages(prompt: str, files: list[FileAttachment],
                    force_text_pdf: bool = False) -> tuple[list, bool]:
    """
    Build the OpenRouter `messages` list. Returns (messages, sent_native_pdf).

    PDFs and images are sent as NATIVE content parts ("file" / "image_url") so
    the model reads the real document. A PDF is instead extracted to text locally
    only when force_text_pdf is set (the per-item fallback after the model/parser
    rejected the native PDF). Plain text files are inlined. sent_native_pdf tells
    the caller whether a PDF was sent natively (so it can decide on the plugin).
    """
    text_prefix = ""
    parts: list = []          # non-text content parts (images + pdf files)
    sent_native_pdf = False

    for f in files:
        mime = f.mime_type.lower()
        if mime.startswith("image/"):
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{f.mime_type};base64,{f.data_b64}"},
            })
        elif mime == "application/pdf":
            if force_text_pdf:
                text = _extract_pdf_text(base64.b64decode(f.data_b64))
                text_prefix += f"[File: {f.filename}]\n{text}\n\n"
            else:
                sent_native_pdf = True
                parts.append({
                    "type": "file",
                    "file": {
                        "filename": f.filename,
                        "file_data": f"data:application/pdf;base64,{f.data_b64}",
                    },
                })
        else:
            raw = base64.b64decode(f.data_b64)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
            text_prefix += f"[File: {f.filename}]\n{text}\n\n"

    full_prompt = text_prefix + prompt
    if parts:
        content: list = [{"type": "text", "text": full_prompt}] + parts
        messages = [{"role": "user", "content": content}]
    else:
        messages = [{"role": "user", "content": full_prompt}]

    return messages, sent_native_pdf


async def _fetch_native_file_models(client: httpx.AsyncClient) -> set:
    """Set of model ids whose architecture.input_modalities includes 'file'.
    Cached for _NATIVE_MODELS_TTL; falls back to the last good value on error."""
    now = time.time()
    cached = _native_models_cache["ids"]
    if cached is not None and now - _native_models_cache["ts"] < _NATIVE_MODELS_TTL:
        return cached
    try:
        resp = await client.get("https://openrouter.ai/api/v1/models", timeout=15)
        data = resp.json().get("data", [])
        ids = {m["id"] for m in data
               if "file" in ((m.get("architecture") or {}).get("input_modalities") or [])}
        if ids:
            _native_models_cache.update(ts=now, ids=ids)
            return ids
    except Exception:
        pass
    return cached if cached is not None else set()


async def _supports_native_file(model: str, client: httpx.AsyncClient) -> bool:
    """Does this model read PDFs natively? On unknown/metadata failure assume yes,
    so we never force the cloudflare parser onto (and override) a native model."""
    ids = await _fetch_native_file_models(client)
    return (model in ids) if ids else True


# A "PDF strategy" decides how a PDF reaches the model for one attempt:
#   "native"     – send the file with NO plugin (the model's own reader; biggest
#                  capacity, e.g. gpt-5.4-nano accepts 512 MB). Native models only.
#   "cloudflare" – send the file + the FREE cloudflare-ai parser. Needed for models
#                  without native file support; lower size ceiling than native.
#   "mistral"    – send the file + the PAID mistral-ocr parser (best for scanned /
#                  image-heavy PDFs). Only used when the user explicitly chooses it.
#   "text"       – don't send the file; inline local pypdf text extraction (free,
#                  lossy on figures/tables). Only used when the user chooses it.
_PDF_ENGINE_FOR = {"cloudflare": "cloudflare-ai", "mistral": "mistral-ocr"}


def _build_request_body(model: str, model_params: dict, prompt: str,
                        files: list[FileAttachment], pdf_strategy: str = "native") -> dict:
    messages, sent_native_pdf = _build_messages(prompt, files,
                                                force_text_pdf=(pdf_strategy == "text"))
    body: dict = {"model": model, "messages": messages}
    body.update({k: v for k, v in (model_params or {}).items() if v is not None})
    if sent_native_pdf and pdf_strategy in _PDF_ENGINE_FOR:
        # Specifying an engine routes the PDF through OpenRouter's parser. We do
        # this only for the cloudflare/mistral strategies; "native" sends no plugin
        # so the model's own (much higher-capacity) file pipeline is used instead.
        body["plugins"] = [{"id": "file-parser", "pdf": {"engine": _PDF_ENGINE_FOR[pdf_strategy]}}]
    return body


async def _pdf_strategy_chain(pdf_mode: str, model: str,
                              files: list[FileAttachment], client: httpx.AsyncClient) -> list:
    """Ordered PDF strategies to try for one item. The free options (native, then
    cloudflare) are chained automatically; the paid (mistral) and lossy (text)
    options are used only when the user explicitly selects them on retry."""
    if not _has_pdf(files):
        return ["native"]                       # no PDF → strategy is irrelevant
    if pdf_mode and pdf_mode != "auto":
        return [pdf_mode]                        # user forced one method
    native = await _supports_native_file(model, client)
    return ["native", "cloudflare"] if native else ["cloudflare"]


def _openrouter_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "LLM Provenance Logger",
    }


def _extract_error_message(resp: httpx.Response) -> str:
    """Pass through OpenRouter's error message; fall back to the raw body."""
    try:
        body = resp.json()
        err = body.get("error")
        if isinstance(err, dict) and err.get("message"):
            return f"OpenRouter {resp.status_code}: {err['message']}"
        if isinstance(err, str):
            return f"OpenRouter {resp.status_code}: {err}"
    except Exception:
        pass
    return f"OpenRouter {resp.status_code}: {resp.text[:500]}"


def _parse_retry_after(resp: httpx.Response):
    val = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


async def _post_openrouter(client: httpx.AsyncClient, api_key: str, body: dict) -> dict:
    """POST one chat-completion. Returns parsed JSON, or raises a classified ItemError."""
    try:
        resp = await client.post(OPENROUTER_URL, headers=_openrouter_headers(api_key), json=body)
    except httpx.RequestError as e:
        raise ItemError(None, f"Could not reach OpenRouter: {e}", retryable=True)

    if resp.status_code == 200:
        return resp.json()

    status = resp.status_code
    message = _extract_error_message(resp)
    if status in FATAL_STATUS:
        raise ItemError(status, message, retryable=False, fatal=True)
    raise ItemError(status, message, retryable=(status in RETRYABLE_STATUS),
                    retry_after=_parse_retry_after(resp))


def _build_record(model: str, model_params: dict, prompt: str,
                  data: dict, files: list[FileAttachment]) -> tuple[dict, str]:
    """
    Build a publishable record (no signature, no researcher_id) and return
    (record, output_text). Computes the per-item hash with the canonical format
    timestamp|model|prompt|output[|sorted file_hashes]. Raises ItemError if the
    response has no usable content.

    `prompt` is the *raw* user prompt — NOT the effective prompt with extracted
    file text prepended. Files are bound to the record by their SHA-256 content
    hash, so the (large) extracted text is never stored: a verifier reconstructs
    the hash from prompt + file hashes, and checks the actual files at Level 2.
    """
    choices = data.get("choices") or []
    if not choices:
        raise ItemError(None, "Model returned no choices", retryable=False)
    choice = choices[0]
    output_text = (choice.get("message") or {}).get("content")
    if output_text is None:
        raise ItemError(None, "Model returned empty content", retryable=False)
    finish_reason = choice.get("finish_reason", "")

    usage_raw = data.get("usage", {}) or {}
    usage = {
        "prompt_tokens": usage_raw.get("prompt_tokens"),
        "completion_tokens": usage_raw.get("completion_tokens"),
        "total_tokens": usage_raw.get("total_tokens"),
        "cost": usage_raw.get("cost"),
    }

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    hash_input = f"{timestamp}|{model}|{prompt}|{output_text}"
    file_meta = []
    if files:
        file_hashes = []
        for f in files:
            fh = hashlib.sha256(base64.b64decode(f.data_b64)).hexdigest()
            file_hashes.append(fh)
            file_meta.append({"filename": f.filename, "file_hash": fh})
        hash_input += "|" + "|".join(sorted(file_hashes))

    hash_hex = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
    record = {
        "id": hash_hex[:8],
        "timestamp": timestamp,
        "model": model,
        "model_params": model_params or {},
        "prompt": prompt,
        "output": output_text,
        "usage": usage,
        "finish_reason": finish_reason,
        "openrouter_id": data.get("id", ""),
        "hash": hash_hex,
    }
    if file_meta:
        record["files"] = file_meta
    return record, output_text


async def _process_one(client: httpx.AsyncClient, api_key: str, model: str,
                       model_params: dict, prompt: str,
                       files: list[FileAttachment], pdf_mode: str = "auto") -> tuple[dict, str]:
    """One logical item: try each PDF strategy (see _pdf_strategy_chain) in order
    until one succeeds. Advance to the next strategy only on a PDF-rejection error
    (PDF_FALLBACK_STATUS) — transient errors propagate to the retry wrapper. Only
    the raw `prompt` is stored/hashed; the file is bound by its content hash, so
    the record is identical no matter which strategy produced the output.
    """
    chain = await _pdf_strategy_chain(pdf_mode, model, files, client)
    last = len(chain) - 1
    for i, strat in enumerate(chain):
        body = _build_request_body(model, model_params, prompt, files, strat)
        try:
            data = await _post_openrouter(client, api_key, body)
            return _build_record(model, model_params, prompt, data, files)
        except ItemError as e:
            if i < last and e.http_status in PDF_FALLBACK_STATUS:
                continue        # free fallback: try the next PDF strategy
            raise


def _backoff_seconds(attempt: int, retry_after) -> float:
    if retry_after is not None:
        return min(retry_after, 30)
    return min(2 ** (attempt - 1), 8) + random.uniform(0, 0.5)


async def _process_one_with_retry(client, api_key, model, model_params, prompt,
                                   files, pdf_mode="auto") -> tuple[dict, str]:
    """Wrap _process_one with bounded retry on transient errors."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return await _process_one(client, api_key, model, model_params,
                                      prompt, files, pdf_mode)
        except ItemError as e:
            if e.fatal or not e.retryable or attempt >= MAX_ATTEMPTS:
                raise
            await asyncio.sleep(_backoff_seconds(attempt, e.retry_after))


# ── Single-prompt mode ────────────────────────────────────────────────────────
async def _run_query_job(job_id: str, request: QueryRequest) -> None:
    """Background task: performs the LLM call and updates _jobs[job_id]."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                record, output_text = await _process_one(
                    client, request.api_key, request.model,
                    request.model_params, request.prompt, request.files)
            except ItemError as e:
                _jobs[job_id]["status"] = "error"
                _jobs[job_id]["error"] = e.message
                return

        receipt: dict = {"record_id": record["id"], "hash": record["hash"]}
        if _sk is not None:
            receipt["signature"] = pcc.sign_hexhash(_sk, record["hash"])

        log_record = {"researcher_id": request.researcher_id, **record}
        researcher_dir = os.path.join(LOG_DIR, request.researcher_id)
        os.makedirs(researcher_dir, exist_ok=True)
        with open(os.path.join(researcher_dir, f"{record['id']}.json"), "w") as fh:
            json.dump(log_record, fh, indent=2)
        with open(os.path.join(researcher_dir, f"{record['id']}_receipt.json"), "w") as fh:
            json.dump(receipt, fh, indent=2)

        _jobs[job_id].update({
            "status": "done",
            "completed_at": record["timestamp"],
            "record": record,
            "receipt": receipt,
            "output": output_text,
        })

    except Exception as e:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(e)


@app.post("/api/query")
async def query(request: QueryRequest):
    if not request.api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required and must be non-empty")
    if not request.researcher_id.strip():
        raise HTTPException(status_code=400, detail="researcher_id is required and must be non-empty")
    if not request.model.strip():
        raise HTTPException(status_code=400, detail="model is required and must be non-empty")
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required and must be non-empty")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "type": "single",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "researcher_id": request.researcher_id,
        "model": request.model,
        "prompt_snippet": request.prompt[:80],
    }

    asyncio.create_task(_run_query_job(job_id, request))
    return {"job_id": job_id}


# ── Batch mode ────────────────────────────────────────────────────────────────
def _safe_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._") or "item"
    return safe[:120]


def _parse_jsonl(text: str) -> list[dict]:
    """Parse JSONL; raise HTTPException(400) listing any unparseable line numbers."""
    items, errors = [], []
    for i, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: {e.msg}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"line {i}: each line must be a JSON object")
            continue
        items.append(obj)
    if errors:
        raise HTTPException(status_code=400, detail="Invalid JSONL — " + "; ".join(errors))
    if not items:
        raise HTTPException(status_code=400, detail="JSONL file contains no requests")
    return items


def _public_job(job: dict) -> dict:
    """Frontend-safe view of a job (strips api_key and heavy retained run state)."""
    if job.get("type") != "batch":
        return job
    items = sorted(job["items_status"].values(), key=lambda x: x["line_index"])
    return {
        "job_id": job["job_id"],
        "type": "batch",
        "status": job["status"],
        "created_at": job["created_at"],
        "researcher_id": job["researcher_id"],
        "batch_name": job.get("batch_name"),
        "model_default": job.get("model_default"),
        "requested_count": job["requested_count"],
        "completed": job["completed"],
        "failed": job["failed"],
        "error": job.get("error"),
        "batch_id": job.get("batch_id"),
        "signed": bool(job.get("signature")),
        "items": [
            {
                "custom_id": it["custom_id"],
                "line_index": it["line_index"],
                "status": it["status"],
                "model": it.get("model"),
                "http_status": it.get("http_status"),
                "error_message": it.get("error_message"),
                "hash": (it.get("record") or {}).get("hash"),
                "usage": (it.get("record") or {}).get("usage"),
                "finish_reason": (it.get("record") or {}).get("finish_reason"),
                "output_snippet": (it.get("output") or "")[:500],
            }
            for it in items
        ],
    }


async def _run_batch_items(job_id: str, custom_ids: list[str]) -> None:
    """Run the given items (initial run or retry) with concurrency cap + retry."""
    job = _jobs[job_id]
    job["status"] = "running"
    sem = asyncio.Semaphore(BATCH_CONCURRENCY)
    abort = asyncio.Event()
    job["_abort_event"] = abort

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def run_item(cid: str):
            spec = job["_specs"][cid]
            it = job["items_status"][cid]
            async with sem:
                if abort.is_set():
                    it.update(status="failed", http_status=None,
                              error_message="Aborted: " + (job.get("error") or "batch aborted"))
                    job["failed"] += 1
                    return
                it["status"] = "running"
                try:
                    record, output = await _process_one_with_retry(
                        client, job["_api_key"], spec["model"], spec["model_params"],
                        spec["prompt"], spec["files"], spec.get("pdf_mode", "auto"))
                    it.update(status="done", record=record, output=output,
                              http_status=None, error_message=None)
                    job["completed"] += 1
                except ItemError as e:
                    if e.fatal:
                        job["error"] = e.message
                        abort.set()
                    it.update(status="failed", record=None, output=None,
                              http_status=e.http_status, error_message=e.message)
                    job["failed"] += 1
                except Exception as e:
                    it.update(status="failed", record=None, output=None,
                              http_status=None,
                              error_message=f"{type(e).__name__}: {e}")
                    job["failed"] += 1

        await asyncio.gather(*(run_item(cid) for cid in custom_ids))

    if job["failed"] == 0:
        await _finalize_batch(job_id)
    elif job["completed"] == 0:
        job["status"] = "error"
        job.setdefault("error", "All items failed.")
    else:
        job["status"] = "awaiting_finalize"


async def _finalize_batch(job_id: str) -> None:
    """Sign the successful set once and write the batch to disk."""
    job = _jobs[job_id]
    items = sorted(job["items_status"].values(), key=lambda x: x["line_index"])
    done_items = [it for it in items if it["status"] == "done"]
    if not done_items:
        job["status"] = "error"
        job["error"] = "No successful items to finalize."
        return

    item_records = [it["record"] for it in done_items]
    batch_hash = hashlib.sha256(
        "|".join(r["hash"] for r in item_records).encode("utf-8")).hexdigest()
    batch_id = batch_hash[:8]
    finalized_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    failed_items = [
        {"custom_id": it["custom_id"], "http_status": it.get("http_status"),
         "error_message": it.get("error_message")}
        for it in items if it["status"] == "failed"
    ]

    batch_record = {
        "job_id": job_id,
        "batch_id": batch_id,
        "batch_name": job.get("batch_name"),
        "created_at": job["created_at"],
        "finalized_at": finalized_at,
        "model_default": job.get("model_default"),
        "requested_count": job["requested_count"],
        "item_count": len(item_records),
        "items": [{"custom_id": it["custom_id"], **it["record"]} for it in done_items],
        "failed_items": failed_items,
        "batch_hash": batch_hash,
    }
    batch_receipt: dict = {"batch_id": batch_id, "batch_hash": batch_hash}
    if _sk is not None:
        batch_receipt["signature"] = pcc.sign_hexhash(_sk, batch_hash)

    researcher_dir = os.path.join(LOG_DIR, job["researcher_id"], f"batch_{batch_id}")
    os.makedirs(researcher_dir, exist_ok=True)

    # The batch is published as exactly two files: the signed record (which
    # already contains every item's output + metadata) and the receipt holding
    # the single signature. Anything a researcher publishes for others to verify
    # must be the bytes we signed, so we deliberately do NOT emit a separate
    # results.jsonl — that would be an unsigned, divergeable copy of the outputs.
    with open(os.path.join(researcher_dir, "batch_record.json"), "w") as f:
        json.dump(batch_record, f, indent=2)
    with open(os.path.join(researcher_dir, "batch_receipt.json"), "w") as f:
        json.dump(batch_receipt, f, indent=2)

    job.update({
        "status": "done",
        "batch_id": batch_id,
        "batch_hash": batch_hash,
        "signature": batch_receipt.get("signature"),
        "finalized_at": finalized_at,
    })
    # Clear secrets / heavy retained state — no further retries after finalize.
    job["_api_key"] = None
    job.pop("_specs", None)


@app.post("/api/batch-query")
async def batch_query(
    api_key: str = Form(...),
    researcher_id: str = Form(...),
    jsonl: UploadFile = File(...),
    files: list[UploadFile] = File(default=[]),
    model: str = Form(""),
    temperature: str = Form(""),
    max_tokens: str = Form(""),
    batch_name: str = Form(""),
):
    if not api_key.strip():
        raise HTTPException(status_code=400, detail="api_key is required and must be non-empty")
    if not researcher_id.strip():
        raise HTTPException(status_code=400, detail="researcher_id is required and must be non-empty")
    batch_name = " ".join(batch_name.split())[:80]   # collapse whitespace, cap length

    raw = (await jsonl.read()).decode("utf-8", errors="replace")
    lines = _parse_jsonl(raw)

    # Default model params from the UI (overridable per line).
    default_params: dict = {}
    if temperature.strip():
        try:
            default_params["temperature"] = float(temperature)
        except ValueError:
            pass
    if max_tokens.strip():
        try:
            default_params["max_tokens"] = int(max_tokens)
        except ValueError:
            pass

    # Map uploaded referenced files by basename (case-insensitive).
    file_map: dict[str, FileAttachment] = {}
    for up in files:
        content = await up.read()
        name = os.path.basename(up.filename or "")
        if not name:
            continue
        mime = up.content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        file_map[name.lower()] = FileAttachment(
            filename=name, mime_type=mime,
            data_b64=base64.b64encode(content).decode("ascii"),
        )

    # Build per-item specs.
    specs: dict[str, dict] = {}
    items_status: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for idx, line in enumerate(lines):
        prompt = line.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise HTTPException(status_code=400,
                                detail=f"line {idx + 1}: 'prompt' is required and must be non-empty")
        cid = str(line.get("custom_id") or f"request-{idx + 1}")
        if cid in seen_ids:
            raise HTTPException(status_code=400, detail=f"duplicate custom_id '{cid}'")
        seen_ids.add(cid)

        item_model = line.get("model") or model
        if not item_model:
            raise HTTPException(
                status_code=400,
                detail=f"line {idx + 1} ({cid}): no model — set a default model or add \"model\" to the line")
        params = {**default_params, **(line.get("model_params") or {})}

        # Resolve referenced files.
        resolved: list[FileAttachment] = []
        for fname in (line.get("files") or []):
            att = file_map.get(os.path.basename(str(fname)).lower())
            if att is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"line {idx + 1} ({cid}): referenced file '{fname}' was not uploaded")
            resolved.append(att)

        specs[cid] = {"line_index": idx, "prompt": prompt, "model": item_model,
                      "model_params": params, "files": resolved, "pdf_mode": "auto"}
        items_status[cid] = {"custom_id": cid, "line_index": idx, "model": item_model,
                             "status": "pending", "record": None, "output": None,
                             "http_status": None, "error_message": None}

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "type": "batch",
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "researcher_id": researcher_id,
        "batch_name": batch_name or None,
        "model_default": model or None,
        "requested_count": len(specs),
        "completed": 0,
        "failed": 0,
        "_api_key": api_key,
        "_specs": specs,
        "items_status": items_status,
    }

    asyncio.create_task(_run_batch_items(job_id, list(specs.keys())))
    return {"job_id": job_id}


@app.post("/api/batch/{job_id}/retry")
async def batch_retry(job_id: str, pdf_mode: str = "auto"):
    """Re-run the failed items. pdf_mode controls how PDFs are sent on this retry:
    "auto" (native→free cloudflare), "mistral" (paid OCR), or "text" (local pypdf)."""
    if pdf_mode not in ("auto", "cloudflare", "mistral", "text", "native"):
        raise HTTPException(status_code=400, detail=f"Invalid pdf_mode '{pdf_mode}'")
    job = _jobs.get(job_id)
    if job is None or job.get("type") != "batch":
        raise HTTPException(status_code=404, detail="Batch job not found")
    if job["status"] not in ("awaiting_finalize", "error"):
        raise HTTPException(status_code=409, detail=f"Cannot retry a batch in status '{job['status']}'")
    if not job.get("_specs"):
        raise HTTPException(status_code=409, detail="Batch already finalized")

    failed_ids = [it["custom_id"] for it in job["items_status"].values()
                  if it["status"] == "failed"]
    if not failed_ids:
        raise HTTPException(status_code=409, detail="No failed items to retry")

    # Reset failed items to pending, apply the chosen PDF method, adjust counter.
    for cid in failed_ids:
        job["items_status"][cid].update(status="pending", http_status=None, error_message=None)
        if cid in job["_specs"]:
            job["_specs"][cid]["pdf_mode"] = pdf_mode
        job["failed"] -= 1
    job.pop("error", None)

    asyncio.create_task(_run_batch_items(job_id, failed_ids))
    return {"job_id": job_id, "retrying": len(failed_ids), "pdf_mode": pdf_mode}


@app.post("/api/batch/{job_id}/cancel")
async def batch_cancel(job_id: str):
    job = _jobs.get(job_id)
    if job is None or job.get("type") != "batch":
        raise HTTPException(status_code=404, detail="Batch job not found")
    if job["status"] not in ("pending", "running"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel a batch in status '{job['status']}'")

    # Signal the running task to stop launching new items.
    job["error"] = "Cancelled by user."
    abort_event = job.get("_abort_event")
    if abort_event:
        abort_event.set()

    # The _run_batch_items gather will drain in-flight calls (≤ BATCH_CONCURRENCY),
    # then call _finalize_batch or set awaiting_finalize on its own.
    # Return immediately so the UI can resume polling.
    return _public_job(job)


@app.post("/api/batch/{job_id}/finalize")
async def batch_finalize(job_id: str):
    job = _jobs.get(job_id)
    if job is None or job.get("type") != "batch":
        raise HTTPException(status_code=404, detail="Batch job not found")
    if job["status"] == "done":
        return _public_job(job)
    if job["status"] != "awaiting_finalize":
        raise HTTPException(status_code=409, detail=f"Cannot finalize a batch in status '{job['status']}'")

    await _finalize_batch(job_id)
    return _public_job(job)


@app.get("/api/job/{job_id}/download")
async def download_batch(job_id: str):
    job = _jobs.get(job_id)
    if job is None or job.get("type") != "batch":
        raise HTTPException(status_code=404, detail="Batch job not found")
    if job.get("status") != "done" or not job.get("batch_id"):
        raise HTTPException(status_code=409, detail="Batch is not finalized yet")

    batch_dir = os.path.join(LOG_DIR, job["researcher_id"], f"batch_{job['batch_id']}")
    if not os.path.isdir(batch_dir):
        raise HTTPException(status_code=404, detail="Batch files not found on disk")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in glob(os.path.join(batch_dir, "**", "*"), recursive=True):
            if os.path.isfile(path):
                zf.write(path, arcname=os.path.relpath(path, batch_dir))
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="batch_{job["batch_id"]}.zip"'},
    )


# ── Job status + log ──────────────────────────────────────────────────────────
def _load_job_from_disk(job_id: str) -> dict | None:
    """Scan logs/ for a finalized batch whose batch_record.json carries this job_id.
    Reconstructs a _jobs-compatible dict and caches it so subsequent lookups are free."""
    if not os.path.isdir(LOG_DIR):
        return None
    for researcher in os.scandir(LOG_DIR):
        if not researcher.is_dir():
            continue
        for batch_dir in os.scandir(researcher.path):
            if not batch_dir.is_dir() or not batch_dir.name.startswith("batch_"):
                continue
            record_path  = os.path.join(batch_dir.path, "batch_record.json")
            receipt_path = os.path.join(batch_dir.path, "batch_receipt.json")
            if not os.path.exists(record_path):
                continue
            try:
                with open(record_path) as f:
                    rec = json.load(f)
                if rec.get("job_id") != job_id:
                    continue
                receipt = {}
                if os.path.exists(receipt_path):
                    with open(receipt_path) as f:
                        receipt = json.load(f)

                # Reconstruct items_status from the record so _public_job() works.
                items_status: dict = {}
                for idx, it in enumerate(rec.get("items", [])):
                    cid = it["custom_id"]
                    items_status[cid] = {
                        "custom_id": cid,
                        "line_index": idx,
                        "status": "done",
                        "model": it.get("model"),
                        "http_status": None,
                        "error_message": None,
                        "record": it,
                        "output": it.get("output"),
                    }
                base_idx = len(items_status)
                for idx, it in enumerate(rec.get("failed_items", [])):
                    cid = it["custom_id"]
                    items_status[cid] = {
                        "custom_id": cid,
                        "line_index": base_idx + idx,
                        "status": "failed",
                        "model": None,
                        "http_status": it.get("http_status"),
                        "error_message": it.get("error_message"),
                        "record": None,
                        "output": None,
                    }

                job = {
                    "job_id": job_id,
                    "type": "batch",
                    "status": "done",
                    "created_at": rec.get("created_at"),
                    "researcher_id": researcher.name,
                    "batch_name": rec.get("batch_name"),
                    "model_default": rec.get("model_default"),
                    "requested_count": rec.get("requested_count", len(items_status)),
                    "completed": rec.get("item_count", 0),
                    "failed": len(rec.get("failed_items", [])),
                    "error": None,
                    "batch_id": rec.get("batch_id"),
                    "batch_hash": rec.get("batch_hash"),
                    "signature": receipt.get("signature"),
                    "finalized_at": rec.get("finalized_at"),
                    "items_status": items_status,
                    "_api_key": None,
                }
                _jobs[job_id] = job   # cache so next poll is instant
                return job
            except Exception:
                continue
    return None


@app.get("/api/job/{job_id}")
async def get_job(job_id: str):
    job = _jobs.get(job_id) or _load_job_from_disk(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found. The server may have been restarted while this job was still running.")
    return _public_job(job)


def _resolve_job(identifier: str) -> dict | None:
    """Find a job by job_id first, then by batch name (case-insensitive). For a
    name, prefer the newest live in-memory match, else the newest finalized batch
    on disk. Returns the full job dict (not the public view) or None."""
    job = _jobs.get(identifier) or _load_job_from_disk(identifier)
    if job is not None:
        return job

    key = identifier.strip().lower()
    if not key:
        return None

    mem = [j for j in _jobs.values()
           if (j.get("batch_name") or "").strip().lower() == key]
    if mem:
        mem.sort(key=lambda j: j.get("created_at") or "", reverse=True)
        return mem[0]

    best = None        # (sort_key, job_id) of the newest matching finalized batch
    if os.path.isdir(LOG_DIR):
        for researcher in os.scandir(LOG_DIR):
            if not researcher.is_dir():
                continue
            for bd in os.scandir(researcher.path):
                if not bd.is_dir() or not bd.name.startswith("batch_"):
                    continue
                rp = os.path.join(bd.path, "batch_record.json")
                if not os.path.exists(rp):
                    continue
                try:
                    with open(rp) as f:
                        rec = json.load(f)
                except Exception:
                    continue
                if (rec.get("batch_name") or "").strip().lower() != key or not rec.get("job_id"):
                    continue
                sort_key = rec.get("finalized_at") or rec.get("created_at") or ""
                if best is None or sort_key > best[0]:
                    best = (sort_key, rec["job_id"])
    return _load_job_from_disk(best[1]) if best else None


@app.get("/api/resolve-job")
async def resolve_job(q: str = ""):
    """Look up a job by job_id OR batch name — used by the 'Check a Job' box."""
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Enter a Job ID or batch name")
    job = _resolve_job(q)
    if job is None:
        raise HTTPException(status_code=404, detail=f"No job found for '{q}' (Job ID or batch name).")
    return _public_job(job)


def _job_summary(job: dict) -> dict:
    """Compact, frontend-safe one-line view of a job (no api_key, no heavy state)."""
    s = {
        "job_id": job.get("job_id"),
        "type": job.get("type"),
        "status": job.get("status"),
        "created_at": job.get("created_at"),
    }
    if job.get("type") == "batch":
        s.update({
            "batch_id": job.get("batch_id"),
            "batch_name": job.get("batch_name"),
            "model": job.get("model_default"),
            "requested_count": job.get("requested_count"),
            "completed": job.get("completed"),
            "failed": job.get("failed"),
        })
    else:
        s.update({"model": job.get("model"), "prompt_snippet": job.get("prompt_snippet")})
    return s


@app.get("/api/jobs")
async def list_jobs(researcher_id: str = ""):
    """All jobs for a researcher: live ones from memory plus finalized batches on
    disk (which survive a server restart). Newest first. Note: researcher_id is a
    self-declared label, not authentication — anyone who knows it can list it."""
    researcher_id = researcher_id.strip()
    if not researcher_id:
        raise HTTPException(status_code=400, detail="researcher_id is required")

    summaries: dict[str, dict] = {}        # keyed by job_id (or batch dir name)
    for job in _jobs.values():
        if job.get("researcher_id") == researcher_id:
            summaries[job["job_id"]] = _job_summary(job)

    researcher_dir = os.path.join(LOG_DIR, researcher_id)
    if os.path.isdir(researcher_dir):
        for batch_dir in os.scandir(researcher_dir):
            if not batch_dir.is_dir() or not batch_dir.name.startswith("batch_"):
                continue
            record_path = os.path.join(batch_dir.path, "batch_record.json")
            if not os.path.exists(record_path):
                continue
            try:
                with open(record_path) as f:
                    rec = json.load(f)
            except Exception:
                continue
            jid = rec.get("job_id")
            if jid and jid in summaries:
                continue               # the live in-memory copy already covers it
            summaries[jid or batch_dir.name] = {
                "job_id": jid,
                "type": "batch",
                "status": "done",
                "created_at": rec.get("created_at"),
                "finalized_at": rec.get("finalized_at"),
                "batch_id": rec.get("batch_id"),
                "batch_name": rec.get("batch_name"),
                "model": rec.get("model_default"),
                "requested_count": rec.get("requested_count"),
                "completed": rec.get("item_count"),
                "failed": len(rec.get("failed_items", [])),
            }

    return sorted(summaries.values(), key=lambda s: s.get("created_at") or "", reverse=True)


@app.get("/api/log")
async def get_log(researcher_id: str = ""):
    if not researcher_id:
        return []
    researcher_dir = os.path.join(LOG_DIR, researcher_id)
    if not os.path.isdir(researcher_dir):
        return []
    records = []
    for path in glob(os.path.join(researcher_dir, "*.json")):
        if path.endswith("_receipt.json"):
            continue
        try:
            with open(path) as f:
                records.append(json.load(f))
        except Exception:
            pass
    records.sort(key=lambda r: r.get("timestamp", ""))
    return records
