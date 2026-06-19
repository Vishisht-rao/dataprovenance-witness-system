from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import base64
import subprocess
import sys
import tempfile
import os

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

UPLOAD_STYLE = {
    "width": "100%",
    "height": "160px",
    "borderWidth": "3px",
    "borderStyle": "dashed",
    "borderRadius": "20px",
    "textAlign": "center",
    "paddingTop": "35px",
    "backgroundColor": "#f8f9fa",
    "cursor": "pointer",
    "transition": "0.3s",
}

DOWNLOAD_GRAY = "#8f9bb8"
VERIFY_BLUE = "#5e89e6"


app.layout = dbc.Container(

    [
        dcc.Download(id="download-public-key"),
        dcc.Download(id="download-canonical"),
        dcc.Download(id="download-receipt"),

        html.H1(
            "Qualtrics Verification Tool",
            className="text-center my-4",
            style={"fontSize": "48px", "fontWeight": "bold"}
        ),

        dcc.Tabs(

            [

                dcc.Tab(
                    label="Generate Dataset & Receipt",

                    children=[

                        html.Br(),

                        html.H3(
                            "Generate Signed Dataset",
                            className="text-center"
                        ),

                        html.Br(),

                        dbc.Input(
                            id="survey-id-input",
                            placeholder="Enter Qualtrics Survey ID",
                            type="text",
                            size="lg"
                        ),

                        html.Br(),

                        html.Div(

                            dbc.Button(
                                "Generate Files",
                                id="generate-button",
                                size="lg",
                                style={
                                    "backgroundColor": VERIFY_BLUE,
                                    "borderColor": VERIFY_BLUE,
                                    "color": "white"
                                }
                            ),

                            className="text-center"
                        ),

                        html.Br(),

                        html.Div(
                            id="generation-result"
                        ),

                        html.Br(),

                        
                        html.Div(
                            [
                                dbc.Button(
                                    "Download Dataset",
                                    id="download-canonical-button",
                                    color="success",
                                    className="me-2"
                                ),

                                dbc.Button(
                                    "Download Receipt",
                                    id="download-receipt-button",
                                    color="primary"
                                )
                            ],
                            id="download-buttons",
                            className="text-center",
                            style={"display": "none"}
                        )

                    ]
                ),

                dcc.Tab(
                    label="Verify Dataset",

                    children=[

                        html.Br(),

                        html.H3(
                            "Dataset File",
                            className="text-center mb-3"
                        ),

                        dcc.Upload(
                            id="dataset-upload",
                            children=html.Div([
                                html.H2("Dataset"),
                                html.P(
                                    "Drag & Drop or Click to Upload"
                                )
                            ]),
                            style=UPLOAD_STYLE
                        ),

                        html.Div(
                            id="dataset-name",
                            className="text-center mt-2 mb-4"
                        ),

                        html.H3(
                            "Receipt File",
                            className="text-center mb-3"
                        ),

                        dcc.Upload(
                            id="receipt-upload",
                            children=html.Div([
                                html.H2("Receipt"),
                                html.P(
                                    "Drag & Drop or Click to Upload"
                                )
                            ]),
                            style=UPLOAD_STYLE
                        ),

                        html.Div(
                            id="receipt-name",
                            className="text-center mt-2 mb-5"
                        ),

                        

                        html.Div(

                            dbc.Button(
                                "Download Public Key",
                                id="download-key-button",
                                size="lg",
                                style={
                                    "backgroundColor": DOWNLOAD_GRAY,
                                    "borderColor": DOWNLOAD_GRAY,
                                    "color": "white"
                                }
                            ),

                            className="text-center mb-4"
                        ),

                        html.Div(

                            dbc.Button(
                                "Verify Dataset",
                                id="verify-button",
                                size="lg",
                                style={
                                    "fontSize": "24px",
                                    "padding": "15px 40px",
                                    "backgroundColor": VERIFY_BLUE,
                                    "borderColor": VERIFY_BLUE,
                                    "color": "white"
                                }
                            ),

                            className="text-center"
                        ),

                        html.Br(),

                        html.Div(
                            id="verification-result"
                        )

                    ]
                )

            ]

        )

    ],

    fluid=True,
    style={
        "paddingTop": "40px",
        "maxWidth": "1200px"
    }

)



def decode_upload(contents, filename, tmp_suffix):
    """Convert Dash upload -> real temp file path"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=tmp_suffix)
    tmp.write(decoded)
    tmp.close()

    return tmp.name

@app.callback(
    Output("generation-result", "children"),
    Output("download-buttons", "style"),
    Input("generate-button", "n_clicks"),
    State("survey-id-input", "value")
)
def generate_files(n_clicks, survey_id):

    if not n_clicks:
        return "", {"display": "none"}

    if not survey_id:
        return (
            dbc.Alert(
                "Please enter a survey ID.",
                color="warning"
            ),
            {"display": "none"}
        )

    cmd = [
        sys.executable,
        "extract_and_sign.py",
        survey_id
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        return (
            dbc.Alert(
                [
                    html.H4("Generation Failed"),
                    html.P(result.stderr)
                ],
                color="danger"
            ),

            {"display": "none"}
        )

    return (
        dbc.Alert(
            [
                html.H4("Files Generated Successfully"),
                html.P(f"Survey {survey_id} was processed.")
            ],
            color="success"
        ),
        {"display": "block"}
    )

@app.callback(
    Output("download-canonical", "data"),
    Input("download-canonical-button", "n_clicks"),
    State("survey-id-input", "value"),
    prevent_initial_call=True
)
def download_dataset(n_clicks, survey_id):

    path = f"outputs/{survey_id}/{survey_id}_canonical.jsonl"
    print("EXISTS:", os.path.exists(path))
    print("PATH:", os.path.abspath(path))
    return dcc.send_file(path)

@app.callback(
    Output("download-receipt", "data"),
    Input("download-receipt-button", "n_clicks"),
    State("survey-id-input", "value"),
    prevent_initial_call=True
)
def download_receipt_file(n_clicks, survey_id):

    path = f"outputs/{survey_id}/{survey_id}_receipt.json"
    print("EXISTS:", os.path.exists(path))
    print("PATH:", os.path.abspath(path))
    return dcc.send_file(path)

@app.callback(
    Output("dataset-upload", "style"),
    Input("dataset-upload", "filename")
)
def style_dataset(filename):
    style = dict(UPLOAD_STYLE)
    if filename:
        style["backgroundColor"] = "#d4edda"
        style["borderColor"] = "#28a745"
    return style


@app.callback(
    Output("receipt-upload", "style"),
    Input("receipt-upload", "filename")
)
def style_receipt(filename):
    style = dict(UPLOAD_STYLE)
    if filename:
        style["backgroundColor"] = "#d4edda"
        style["borderColor"] = "#28a745"
    return style


@app.callback(
    Output("dataset-name", "children"),
    Input("dataset-upload", "filename")
)
def show_dataset(filename):
    if not filename:
        return ""
    return html.Div(f"Selected: {filename}", style={
        "fontSize": "18px",
        "fontWeight": "bold",
        "color": "#28a745"
    })


@app.callback(
    Output("receipt-name", "children"),
    Input("receipt-upload", "filename")
)
def show_receipt(filename):
    if not filename:
        return ""
    return html.Div(f"Selected: {filename}", style={
        "fontSize": "18px",
        "fontWeight": "bold",
        "color": "#28a745"
    })


@app.callback(
    Output("verification-result", "children"),
    Input("verify-button", "n_clicks"),
    State("dataset-upload", "contents"),
    State("dataset-upload", "filename"),
    State("receipt-upload", "contents"),
    State("receipt-upload", "filename")
)
def verify(n_clicks, ds_contents, ds_name, rc_contents, rc_name):

    if not n_clicks:
        return ""

    if not ds_contents or not rc_contents:
        return dbc.Alert(
            "Please upload both dataset and receipt.",
            color="warning",
            style={"fontSize": "20px"}
        )

    # write temp files
    ds_path = decode_upload(ds_contents, ds_name, ".jsonl")
    rc_path = decode_upload(rc_contents, rc_name, ".json")

    cmd = [
        sys.executable,
        "verify_data.py",
        "--data", ds_path,
        "--receipt", rc_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    success = result.returncode == 0

    if success:
        return dbc.Alert(
            [
                html.H2("✓ Verification Successful. The signature matches the data."),
            ],
            color="success",
            style={"fontSize": "20px", "marginTop": "20px"}
        )

    else:
        return dbc.Alert(
            [
                html.H2("✗ Verification Failed. The signature does not match the data."),
            ],
            color="danger",
            style={"fontSize": "20px", "marginTop": "20px"}
        )

@app.callback(
    Output("download-public-key", "data"),
    Input("download-key-button", "n_clicks"),
    prevent_initial_call=True
)
def download_public_key(n_clicks):
    return dcc.send_file("witness_pk.ed25519")

if __name__ == "__main__":
    app.run(debug=True, port=8052)