"""
Verification UI for the LLM Provenance Logger.

Same stack/design as qualtrics_prototype/verification_ui.py (Dash +
dash-bootstrap-components, shelling out to the CLI tools). Two tabs:

  • Merge Receipts — upload several record+receipt pairs (singles and/or
    batches) and produce ONE unified record + ONE new signature over all of
    their LLM requests (calls merge.py).
  • Verify — upload a record + receipt + optionally the referenced files; the
    result states whether it was a complete Level 2 verification or only Level 1
    (calls verify.py --json).

Run from this directory:  python verification_ui.py   ->  http://localhost:8053
"""

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MERGE_OUT_DIR = os.path.join(SCRIPT_DIR, "merged_outputs")
PUBLIC_KEY_PATH = os.path.join(SCRIPT_DIR, "keys", "witness_pk.ed25519")

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
app.title = "LLM Provenance Verification Tool"

UPLOAD_STYLE = {
    "width": "100%",
    "height": "120px",
    "borderWidth": "3px",
    "borderStyle": "dashed",
    "borderRadius": "20px",
    "textAlign": "center",
    "paddingTop": "28px",
    "backgroundColor": "#f8f9fa",
    "cursor": "pointer",
    "transition": "0.3s",
}

DOWNLOAD_GRAY = "#8f9bb8"
VERIFY_BLUE = "#5e89e6"


def upload_box(upload_id, title, multiple=False):
    return html.Div([
        dcc.Upload(
            id=upload_id,
            children=html.Div([html.H4(title), html.P("Drag & Drop or Click to Upload")]),
            style=UPLOAD_STYLE,
            multiple=multiple,
        ),
        html.Div(id=f"{upload_id}-name", className="text-center mt-2 mb-4"),
    ])


app.layout = dbc.Container(
    [
        dcc.Store(id="merge-paths"),
        dcc.Download(id="download-merged-record"),
        dcc.Download(id="download-merged-receipt"),
        dcc.Download(id="download-public-key"),

        html.H1(
            "LLM Provenance Verification Tool",
            className="text-center my-4",
            style={"fontSize": "44px", "fontWeight": "bold"},
        ),

        dcc.Tabs([

            # ---------------- Tab 1: Merge Receipts ----------------
            dcc.Tab(label="Merge Receipts", children=[
                html.Br(),
                html.H3("Merge Signed Records", className="text-center"),
                html.P(
                    "Upload several record + receipt pairs (single records and/or batches). "
                    "Every pair is re-verified, then all of their LLM requests are combined into "
                    "one record and signed once. If any pair fails to verify, the whole merge is "
                    "refused.",
                    className="text-center text-muted",
                    style={"maxWidth": "780px", "margin": "0 auto 24px"},
                ),
                upload_box("merge-records", "Record files", multiple=True),
                upload_box("merge-receipts", "Receipt files", multiple=True),
                html.Div(
                    dbc.Button(
                        "Merge & Sign", id="merge-button", size="lg",
                        style={"fontSize": "22px", "padding": "12px 36px",
                               "backgroundColor": VERIFY_BLUE, "borderColor": VERIFY_BLUE,
                               "color": "white"},
                    ),
                    className="text-center",
                ),
                html.Br(),
                html.Div(id="merge-result"),
                html.Br(),
                html.Div(
                    [
                        dbc.Button("Download Merged Record", id="download-merged-record-button",
                                   color="success", className="me-2"),
                        dbc.Button("Download Merged Receipt", id="download-merged-receipt-button",
                                   color="primary"),
                    ],
                    id="merge-download-buttons", className="text-center",
                    style={"display": "none"},
                ),
            ]),

            # ---------------- Tab 2: Verify ----------------
            dcc.Tab(label="Verify", children=[
                html.Br(),
                html.H3("Verify a Record", className="text-center"),
                html.P(
                    "Upload a record and its receipt. Optionally upload the referenced files to "
                    "additionally check their content (Level 2).",
                    className="text-center text-muted",
                    style={"maxWidth": "780px", "margin": "0 auto 24px"},
                ),
                upload_box("verify-record", "Record"),
                upload_box("verify-receipt", "Receipt"),
                upload_box("verify-files", "Files (optional)", multiple=True),
                html.Div(
                    dbc.Button(
                        "Download Public Key", id="download-key-button", size="lg",
                        style={"backgroundColor": DOWNLOAD_GRAY, "borderColor": DOWNLOAD_GRAY,
                               "color": "white"},
                    ),
                    className="text-center mb-4",
                ),
                html.Div(
                    dbc.Button(
                        "Verify", id="verify-button", size="lg",
                        style={"fontSize": "24px", "padding": "15px 40px",
                               "backgroundColor": VERIFY_BLUE, "borderColor": VERIFY_BLUE,
                               "color": "white"},
                    ),
                    className="text-center",
                ),
                html.Br(),
                html.Div(id="verification-result"),
            ]),

        ]),
    ],
    fluid=True,
    style={"paddingTop": "30px", "maxWidth": "1100px", "paddingBottom": "60px"},
)


# ----------------------------- helpers -----------------------------

def _as_list(contents, filename):
    """Normalize a dcc.Upload value to parallel lists (handles multiple=True/False)."""
    if contents is None:
        return [], []
    if isinstance(contents, str):
        return [contents], [filename]
    return list(contents), list(filename or [None] * len(contents))


def decode_uploads(contents, filename, dest_dir, start=0):
    """Write uploaded file(s) into dest_dir under unique names; return their paths."""
    conts, names = _as_list(contents, filename)
    paths = []
    for i, (c, n) in enumerate(zip(conts, names)):
        _, b64 = c.split(",", 1)
        safe = f"{start + i}_{os.path.basename(n or 'file')}"
        path = os.path.join(dest_dir, safe)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        paths.append(path)
    return paths


def _highlight(filename):
    style = dict(UPLOAD_STYLE)
    if filename:
        style["backgroundColor"] = "#d4edda"
        style["borderColor"] = "#28a745"
    return style


def _names(filename):
    if not filename:
        return ""
    names = filename if isinstance(filename, list) else [filename]
    return html.Div(
        f"Selected: {', '.join(names)}",
        style={"fontSize": "16px", "fontWeight": "bold", "color": "#28a745"},
    )


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR)


# ------------------------- upload styling/names -------------------------

for _uid in ("merge-records", "merge-receipts", "verify-record", "verify-receipt", "verify-files"):
    app.callback(Output(_uid, "style"), Input(_uid, "filename"))(_highlight)
    app.callback(Output(f"{_uid}-name", "children"), Input(_uid, "filename"))(_names)


# ------------------------------ Merge ------------------------------

@app.callback(
    Output("merge-result", "children"),
    Output("merge-download-buttons", "style"),
    Output("merge-paths", "data"),
    Input("merge-button", "n_clicks"),
    State("merge-records", "contents"), State("merge-records", "filename"),
    State("merge-receipts", "contents"), State("merge-receipts", "filename"),
    prevent_initial_call=True,
)
def do_merge(n_clicks, rec_contents, rec_names, rc_contents, rc_names):
    hidden = {"display": "none"}
    if not rec_contents or not rc_contents:
        return (dbc.Alert("Please upload at least one record file and one receipt file.",
                          color="warning", style={"fontSize": "18px"}),
                hidden, None)

    tmp = tempfile.mkdtemp(prefix="merge_in_")
    try:
        record_paths = decode_uploads(rec_contents, rec_names, tmp, 0)
        receipt_paths = decode_uploads(rc_contents, rc_names, tmp, len(record_paths))
        cmd = [sys.executable, "merge.py", "--json",
               "--records", *record_paths,
               "--receipts", *receipt_paths,
               "--out", MERGE_OUT_DIR]
        result = _run(cmd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if result.returncode != 0:
        return (dbc.Alert(
            [html.H4("Merge refused"),
             html.P(result.stderr.strip() or "Unknown error", style={"whiteSpace": "pre-wrap"})],
            color="danger", style={"fontSize": "18px"}),
            hidden, None)

    summary = json.loads(result.stdout.strip().splitlines()[-1])
    msg = dbc.Alert(
        [html.H4("✓ Merged & signed"),
         html.P(f"Combined {summary['source_count']} source(s) into "
                f"{summary['item_count']} LLM request(s)."),
         html.P(f"merged_id: {summary['merged_id']}", className="text-muted mb-0")],
        color="success", style={"fontSize": "18px"})
    return msg, {"display": "block"}, {"record": summary["record_path"],
                                       "receipt": summary["receipt_path"]}


@app.callback(
    Output("download-merged-record", "data"),
    Input("download-merged-record-button", "n_clicks"),
    State("merge-paths", "data"),
    prevent_initial_call=True,
)
def dl_merged_record(n_clicks, paths):
    if paths and paths.get("record"):
        return dcc.send_file(paths["record"])
    return None


@app.callback(
    Output("download-merged-receipt", "data"),
    Input("download-merged-receipt-button", "n_clicks"),
    State("merge-paths", "data"),
    prevent_initial_call=True,
)
def dl_merged_receipt(n_clicks, paths):
    if paths and paths.get("receipt"):
        return dcc.send_file(paths["receipt"])
    return None


# ------------------------------ Verify ------------------------------

def _render_verification(res):
    mode = res.get("mode", "?")
    f = res.get("files", {})
    recorded = f.get("recorded_total", 0)
    matched = f.get("matched", 0)
    detail = res.get("level1_detail", "")

    def alert(color, head, sub):
        body = [html.H2(head, style={"fontSize": "26px"})]
        if sub:
            body.append(html.P(sub, className="mb-1"))
        body.append(html.P(f"{detail} · mode: {mode}", className="text-muted mb-0",
                            style={"fontSize": "14px"}))
        return dbc.Alert(body, color=color, style={"fontSize": "18px", "marginTop": "20px"})

    if not res.get("level1_ok"):
        return alert("danger", "✗ Verification Failed",
                     "The signature does not match the record (Level 1 failed).")

    # Level 1 passed; a supplied file matching nothing is still a hard failure.
    if f.get("mismatched"):
        bad = ", ".join(f["mismatched"])
        return alert("danger", "✗ Level 2 Failed",
                     f"Signature is valid, but an uploaded file matches nothing in the record: {bad}.")

    level2 = res.get("level2")
    if level2 == "complete":
        return alert("success", "✓ Complete Level 2 Verification",
                     f"Signature is valid AND all {recorded} referenced file(s) match.")
    if level2 == "na":
        return alert("success", "✓ Level 1 Verified",
                     "Signature is valid. This record references no files, so there is nothing "
                     "to check at Level 2.")
    if level2 == "none":
        return alert("info", "✓ Level 1 Verified (signature only)",
                     f"Signature is valid. This record references {recorded} file(s) — upload them "
                     "to perform full Level 2 (content) verification.")
    # partial (some matched, some still missing)
    return alert("info", "✓ Level 1 Verified + Partial Level 2",
                 f"Signature is valid and {matched} of {recorded} referenced file(s) matched. "
                 "Upload the remaining file(s) for complete Level 2.")


@app.callback(
    Output("verification-result", "children"),
    Input("verify-button", "n_clicks"),
    State("verify-record", "contents"), State("verify-record", "filename"),
    State("verify-receipt", "contents"), State("verify-receipt", "filename"),
    State("verify-files", "contents"), State("verify-files", "filename"),
    prevent_initial_call=True,
)
def do_verify(n_clicks, rec_c, rec_n, rcpt_c, rcpt_n, files_c, files_n):
    if not rec_c or not rcpt_c:
        return dbc.Alert("Please upload both a record and a receipt.",
                         color="warning", style={"fontSize": "18px"})

    tmp = tempfile.mkdtemp(prefix="verify_in_")
    try:
        record_path = decode_uploads(rec_c, rec_n, tmp, 0)[0]
        receipt_path = decode_uploads(rcpt_c, rcpt_n, tmp, 1)[0]
        cmd = [sys.executable, "verify.py", "--json", record_path, receipt_path]
        file_paths = decode_uploads(files_c, files_n, tmp, 2)
        if file_paths:
            cmd += ["--files", *file_paths]
        result = _run(cmd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    try:
        res = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return dbc.Alert(
            [html.H4("Could not run verification"),
             html.P((result.stderr or result.stdout or "Unknown error").strip(),
                    style={"whiteSpace": "pre-wrap"})],
            color="danger", style={"fontSize": "18px"})

    return _render_verification(res)


@app.callback(
    Output("download-public-key", "data"),
    Input("download-key-button", "n_clicks"),
    prevent_initial_call=True,
)
def download_public_key(n_clicks):
    return dcc.send_file(PUBLIC_KEY_PATH)


if __name__ == "__main__":
    app.run(debug=True, port=8053)
