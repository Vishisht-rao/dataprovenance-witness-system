from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

def tutorial_card(title, children):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2(
                    title,
                    className="mb-4",
                    style={
                        "color": "#2c3e50",
                        "fontWeight": "700",
                        "fontSize": "34px"
                    }
                ),
                *children
            ]
        ),
        className="shadow-lg mb-5",
        style={
            "borderRadius": "24px",
            "border": "1px solid #eef2ff",
            "backgroundColor": "white",
            "padding": "10px"
        }
    )

IMAGE_STYLE = {
    "width": "100%",
    "maxWidth": "950px",
    "display": "block",
    "margin": "25px auto",
    "borderRadius": "15px",
    "boxShadow": "0 6px 20px rgba(0,0,0,0.12)"
}
TEXT_STYLE = {
    "fontSize": "26px",
    "lineHeight": "1.8"
}

app.layout = dbc.Container(

    [

        dbc.Card(

    dbc.CardBody([

        html.H1(
            "Provenance Tutorials",
            className="text-center my-5",
            style={
                "fontWeight": "700",
                "color": "#2c3e50"
            }
        ),

    ]),

    className="shadow-sm mb-4",
    style={
        "background": "linear-gradient(135deg,#eef4ff,#f8f5ff)",
        "borderRadius": "20px"
    }
),

        dcc.Tabs(
            colors={
                "border": "#d9e4ff",
                "primary": "#5e89e6",
                "background": "#f8f9ff"
            },
            children=[

            dcc.Tab(
            label="Qualtrics Setup Tutorial",
            children=[

                html.Br(),

                html.H1("Qualtrics Setup Guide for Provenance Logging"),

                html.Hr(),

                tutorial_card(
                    "Initial Notes",
                    [
                        html.P("1. Researchers need access to the paid version of Qualtrics.", style=TEXT_STYLE),
                        html.P("2. CMU users can access it through their Andrew credentials.",style=TEXT_STYLE),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 1: Log In to Qualtrics",
                    [
                        html.P(
                            "1. Navigate to the CMU Qualtrics portal via https://cmu.yul1.qualtrics.com/.",
                            style=TEXT_STYLE
                        ),
                        html.P(
                            "2. Sign in using your Andrew ID credentials.", style=TEXT_STYLE
                        ),
                        html.P(
                            "3. Select Create New Project.", style=TEXT_STYLE
                        ),

                        # html.Img(
                        #     src="/assets/project.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto",
                        #         "borderRadius": "12px"
                        #     }
                        # )

                        html.Img(
                            src="/assets/project.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 2: Create a Survey",
                    [
                        html.P(
                            "1. Choose Survey.", style=TEXT_STYLE
                        ),
                        
                        # html.Img(
                        #     src="/assets/survey.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/survey.png",
                            style={"width": "100%"}
                        ),
                        html.P(
                            "2. Enter a project name, and add one or more questions.", style=TEXT_STYLE
                        ),
                        html.P(
                            "3. Add one or more questions.", style=TEXT_STYLE
                        ),
                        # html.Img(
                        #     src="/assets/questions.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/questions.png",
                            style=IMAGE_STYLE
                        ),
                    ]
                ),

                
                html.Hr(),

                tutorial_card(
                    "Step 3: Open the Workflows Tab",
                    [
                        # html.P("1. Open your survey project."),

                        html.P("1. Select the Workflows tab.", style=TEXT_STYLE),

                        html.P("2. Click Create Workflow.", style=TEXT_STYLE),

                        # html.Img(
                        #     src="/assets/newWorkflow.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/newWorkflow.png",
                            style=IMAGE_STYLE
                        ),
                    ]
                ),
            

                html.Hr(),

                tutorial_card(
                    "Step 4: Configure the Workflow Trigger",
                    [
                        html.P("1. Click Browse Templates.", style=TEXT_STYLE),
                        html.P("2. Select 'Start a workflow when a survey response is received or updated'.", style=TEXT_STYLE),
                        html.P("3. Verify the correct survey is selected.", style=TEXT_STYLE),
                        html.P("4. Enter a workflow name.", style=TEXT_STYLE),

                        # html.Img(
                        #     src="/assets/workflow.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/workflow.png",
                            style={"width": "100%"}
                        ),

                    ]
                ),
                
                html.Hr(),

                tutorial_card(
                    "Step 5: Add an Email Task",
                    [
                        html.H2(),

                        html.P("1. Click the small plus button.", style=TEXT_STYLE),
                        html.P("2. Select Add Task.", style=TEXT_STYLE),

                    #    html.Img(
                    #         src="/assets/task.png",
                    #         style={
                    #             "width": "100%",
                    #             "maxWidth": "900px",
                    #             "display": "block",
                    #             "margin": "20px auto"
                    #         }
                    #     ),
                        html.Img(
                            src="/assets/task.png",
                            style={"width": "100%"}
                        ),
                        html.P("3. Search for and select Email.", style=TEXT_STYLE),
                        html.Img(
                            src="/assets/addedStep.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 6: Configure Email Settings",
                    [
                        html.P("Use the following values:", style=TEXT_STYLE),
                        dbc.Table.from_dataframe(
                            pd.DataFrame({
                                "Field": [
                                    "To",
                                    "From",
                                    "From Name",
                                    "Reply-To",
                                    "When"
                                ],
                                "Value": [
                                    "middlewarequaltrics@gmail.com",
                                    "noreply@qemailserver.com",
                                    "Your Name",
                                    "vsrao@cs.cmu.edu",
                                    "Immediately"
                                ]
                            }),
                            bordered=True,
                            striped=True
                        ),

                        # html.Img(
                        #     src="/assets/email.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/email.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),
                tutorial_card(
                    "Step 7: Set the Subject Line and Email Body",
                    [
                        html.P("1. The email subject should be the Survey ID.", style=TEXT_STYLE),
                        html.P("   The Survey ID begins with SV_ and can be found in the survey URL.", style=TEXT_STYLE),
                        # html.Img(
                        #     src="/assets/SV.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/SV.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),
                tutorial_card( 
                    "Step 8: Additional changes",
                    [

                        html.P("1. Fill in the email body with a blank space.", style=TEXT_STYLE),
                        html.P("2. Enable Include Response Report.", style=TEXT_STYLE),
                        html.P("3. Embedded Data should be Survey Flow.", style=TEXT_STYLE),
                        html.P("4. Save the workflow.", style=TEXT_STYLE),

                        # html.Img(
                        #     src="/assets/embedded.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/embedded.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),


                html.Hr(),

                tutorial_card(
                    "Step 9: Publish the Survey",
                    [
                        html.P("1. Returning back to the Survey page, click Publish in the upper-right corner.", style=TEXT_STYLE),
                        html.P("2. Confirm publication.", style=TEXT_STYLE),
                        html.P("The survey must be published before it can collect responses.", style=TEXT_STYLE),

                        # html.Img(
                        #     src="/assets/publish.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/publish.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),
                
                html.Hr(),

                tutorial_card(
                    "Step 10: Activate the Workflow",
                    [
                        html.P("1. Open your survey in Qualtrics.", style=TEXT_STYLE),
                        html.P("2. Navigate to Distributions.", style=TEXT_STYLE),
                        html.P("3. Distribute to participants using any Qualtrics-supported method.", style=TEXT_STYLE),
                        html.P("4. The workflow will trigger whenever a participant submits a response, regardless of how the participant accessed the survey.", style=TEXT_STYLE),

                        html.H3("Example"),

                        html.Ol([
                            html.Li("Select the Anonymous Link section.", style=TEXT_STYLE),
                            html.Li("Click Copy Link.", style=TEXT_STYLE),
                            html.Li("Share the link with participants.", style=TEXT_STYLE)
                        ]),

                        # html.Img(
                        #     src="/assets/createSurvey.png",
                        #     style={
                        #         "width": "100%",
                        #         "maxWidth": "900px",
                        #         "display": "block",
                        #         "margin": "20px auto"
                        #     }
                        # ),
                        html.Img(
                            src="/assets/createSurvey.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

    

            ]
        ),

        dcc.Tab(
            label="Qualtrics Verification Tutorial",

            children=[

                html.H1("Tutorial for Verfication Interface"),

                html.Hr(),

                tutorial_card(
                    "Step 1: Generate Files",
                    [
                        html.P(
                            "Navigate to the Generate Dataset & Receipt tab.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/generate_tab.png",
                            style={"width": "100%"}
                        ),
                            ]
                ),

                html.Hr(),

                tutorial_card(
                   "Step 2: Enter a Survey ID",
                    [
                        html.P(
                            "Enter the Survey ID associated with your Qualtrics survey.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/SVInput.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                
                html.Hr(),
                tutorial_card(
                    "Step 3: Generate the Signed Files",
                    [

                        html.P(
                            "Click Generate Files. The system will create a canonical dataset and a receipt.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/generateFiles.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 4: Download the Files",
                    [
                        html.P(
                            [
                                "Download both the dataset and ",
                                html.A(
                                    "receipt",
                                    href="#receipt"
                                ),
                                " files."
                            ], style=TEXT_STYLE
                        ),


                        html.Img(
                            src="/assets/download.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 5: Verify Dataset Tab",
                    [
                        html.P(
                            "Open the Verify Dataset tab.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/verificationPage.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 6: Upload the Dataset",
                    [
                        html.P(
                            "Drag and drop or click to upload the downloaded dataset and receipt files.", style=TEXT_STYLE
                        ),
                        html.P(
                            "A green highlight indicates that the file has been successfully selected.", style=TEXT_STYLE
                        ),
                        html.Img(
                            src="/assets/upload1.png",
                            style={"width": "100%"}
                        ),

                        html.Img(
                            src="/assets/upload.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                tutorial_card(
                    "Step 7: Verify the Dataset",
                    [
                        html.P(
                            "Click Verify Dataset.", style=TEXT_STYLE
                        ),
                        html.P(
                            "The verification tool will compare the uploaded dataset against the cryptographic signature stored in the receipt.", style=TEXT_STYLE
                        ),
                        html.Img(
                            src="/assets/verifyDataset.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                tutorial_card(
                    "Step 8: Successful Verification",
                    [
                        html.P(
                            "If the dataset has not been modified, the tool will display: ✓ Verification Successful. The signature matches the data.", style=TEXT_STYLE
                        ),
                        html.P(
                            "This confirms that the dataset is authentic and unchanged.", style=TEXT_STYLE
                        ),
                        html.Img(
                            src="/assets/success.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                tutorial_card(
                    "Step 9: Failed Verification",
                    [
                        html.P(
                            "If either the dataset contents have been modified or the receipt/signature has been altered, the tool will display", style=TEXT_STYLE
                        ),
                        html.P("X Verification Failed. The signature does not match the data.", style=TEXT_STYLE),

                        html.P(
                            "This indicates that the dataset can no longer be verified against the original signed version.", style=TEXT_STYLE
                        ),
                        html.Img(
                            src="/assets/Failure.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),
                tutorial_card(
                    "Step 10: Download the Public Key",
                    [
                        html.P(
                            [
                                "To independently verify signatures, click ",
                                html.A(
                                    "Download Public Key",
                                    href="#public-key"
                                ),
                                "."
                            ], style=TEXT_STYLE
                        ),
                        
                        html.P("This downloads the public verification key used.", style=TEXT_STYLE),

                        html.Img(
                            src="/assets/publicKey.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),


                html.Hr(),

                

                html.H1("Definitions"),

                html.H3(
                            "Public Key",
                            id="public-key"
                        ),

                html.P(
                    "The public key is used to verify that a receipt was signed by Witness.", style=TEXT_STYLE
                ),

                html.H3(
                            "Receipt",
                            id="receipt"
                        ),

                html.P(
                    "The receipt contains the cryptographic signature generated for a dataset.", style=TEXT_STYLE
                ),

                html.H3(
                            "Canonical Dataset",
                            id="canonical-dataset"
                        ),

                html.P(
                    "The canonical dataset is the normalized version of the survey responses that is used when generating the signature.", style=TEXT_STYLE
                )

            ]

            ),

        dcc.Tab(
            label="LLM Provenance Tutorial",

            children=[

                html.H1("Tutorial for LLM Provenance"),

                html.Hr(),

                dcc.Tabs(
                    colors={
                        "border": "#d9e4ff",
                        "primary": "#5e89e6",
                        "background": "#f8f9ff"
                    },
                    children=[

            dcc.Tab(
            label="Single Prompt",
            children=[

                html.Br(),

                tutorial_card(
                    "Step 1: Enter Your Researcher ID",
                    [
                        html.P(
                            "In the Researcher ID field, enter your assigned identifier.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/researchID.png",
                            style={"width": "100%"}
                        ),
                            ]
                ),

                html.Hr(),

                tutorial_card(
                   "Step 2: Enter Your API Key",
                    [
                        html.P(
                            "Paste your OpenRouter API key into the OpenRouter API Key field.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/APIKey.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                
                html.Hr(),
                tutorial_card(
                    "Step 3: Select a Model",
                    [

                        html.P(
                            "Choose the AI model you would like to use.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/chooseModel.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 4: Choose Optional Settings",
                    [
                        html.P(
                            "1. Temperature.", style=TEXT_STYLE
                        ),
                        html.P(
                            "2. Max Tokens.", style=TEXT_STYLE
                        ),


                        html.Img(
                            src="/assets/optionalSettings.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 5: Enter Your Prompt",
                    [
                        html.P(
                            "Type your prompt into the Prompt / Input box.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/inputPrompt.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 6: Attach AnySupporting Files",
                    [
                        html.P(
                            "If your task requires additional materials, you may upload files.", style=TEXT_STYLE
                        ),
                        
                        html.Img(
                            src="/assets/uploadAdditionalDocs.png",
                            style={"width": "100%"}
                        ),

                    ]
                ),

                tutorial_card(
                    "Step 7: Submit Your Request",
                    [
                        html.P(
                            "Click Submit.", style=TEXT_STYLE
                        ),
                        html.P(
                            "After submitting, a Job ID will be displayed. This Job ID can be used to retrieve your result later if needed.", style=TEXT_STYLE
                        ),
                        html.Img(
                            src="/assets/submitJobID.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                tutorial_card(
                    "Viewing Previous Records",
                    [
                        html.P(
                            "To view previously generated provenance records, click View My Provenance Log.", style=TEXT_STYLE
                        ),
                        
                        html.Img(
                            src="/assets/provenanceLog.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                tutorial_card(
                    "Resuming a Previous Job",
                    [
                        html.P(
                            "If you close the page before a request finishes processing, you can retrieve it later using the Job ID.", style=TEXT_STYLE
                        ),
                        html.P(
                            "If the job has completed and is still available, the result and provenance record will be displayed.", style=TEXT_STYLE
                        ),
                        html.Img(
                            src="/assets/checkJobStatus.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

            ]
            ),

            dcc.Tab(
            label="Batch Processing",
            children=[

                html.Br(),

                tutorial_card(
                    "Why Batch Processing Exists",
                    [
                        html.P(
                            "OpenRouter has no native batch API. Batch Processing instead runs many requests as real-time calls under the hood, but binds the whole set together under one signature.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Use this mode when you have many prompts (for example, one prompt per paper across a folder of PDFs) and want a single signed bundle covering all of them, instead of running and publishing each request separately.", style=TEXT_STYLE
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 1: Switch to Batch Processing",
                    [
                        html.P(
                            "In the Workflow Mode dropdown, select Batch Processing (JSONL).", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchWorkflowMode.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 2: Fill In the Configuration Fields",
                    [
                        html.P(
                            "Enter your Researcher ID and OpenRouter API Key, same as in the Single Prompt workflow.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Enter a default Model, Temperature, and Max Tokens. These apply to every line in your batch unless a specific line overrides them.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchConfigFields.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 3: Name Your Batch (Optional)",
                    [
                        html.P(
                            "Enter a Batch Name. This is just a label so you can find this batch later under My Jobs or Check a Job. It is not required.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchName.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 4: Choose How to Provide Your Requests",
                    [
                        html.P(
                            "Choose Upload a JSONL file if you already have a file with one request per line.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Choose Same prompt for every file if you want to run one shared prompt across several uploaded files (for example, the same review prompt across many PDFs).", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchModeChoice.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 5a: Upload a JSONL File",
                    [
                        html.P(
                            "If you chose Upload a JSONL file, click the upload zone and select your .jsonl file.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Each line of the file must be a JSON object with at least a prompt field. You may also include custom_id, model, model_params, and files (a list of filenames referenced by that line).", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchJsonlUpload.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 5b: Or Use a Shared Prompt",
                    [
                        html.P(
                            "If you chose Same prompt for every file, type the shared prompt into the Shared Prompt box. One request will be generated per uploaded file, all using this same prompt.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchHelperMode.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 6: Upload Any Referenced Files",
                    [
                        html.P(
                            "Upload any files your JSONL lines reference by name, or, in shared prompt mode, the files you want one request generated per file for.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchFilesUpload.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 7: Review the Batch Summary",
                    [
                        html.P(
                            "Check the summary line showing how many requests and files will be submitted before continuing.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchSummary.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 8: Submit the Batch",
                    [
                        html.P(
                            "Click Submit Batch. A Job ID is displayed immediately, the same way it is for a single prompt request.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/submitBatchButton.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 9: Track Progress",
                    [
                        html.P(
                            "The Job ID banner lets you copy the Job ID and shows polling status while the batch runs in the background.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchJobBanner.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 10: View Batch Results and Cancel",
                    [
                        html.P(
                            "The Batch Results panel shows progress across all items, including how many have completed and how many have failed. While the batch is still running, a Cancel batch button is shown here too. In-flight calls finish, but no new ones are started.", style=TEXT_STYLE
                        ),
                        html.P(
                            "If some items fail once the batch finishes, this same panel instead shows a Retry failed button (with a PDF handling method selector for the retry) and a Sign & Save button, so you can retry the failures before finalizing.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchResultsProgress.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 11: Download the Batch",
                    [
                        html.P(
                            "If every item succeeds, the batch is signed and saved automatically as soon as it finishes, no extra click required. The panel then shows Download record + receipt (ZIP) directly.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Click it to get a zip file containing batch_record.json and batch_receipt.json. These two files together are the entire publishable bundle.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchDownloadZip.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 12: Inspect Individual Items",
                    [
                        html.P(
                            "Scroll through the item list to see the per-item status, model, and a snippet of the output for every line in the batch.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/batchItemsList.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

            ]
            ),

                    ]
                ),

            ]

            ),

        dcc.Tab(
            label="LLM Verification Tutorial",

            children=[

                html.H1("Tutorial for LLM Verification Tool"),

                html.Hr(),

                dcc.Tabs(
                    colors={
                        "border": "#d9e4ff",
                        "primary": "#5e89e6",
                        "background": "#f8f9ff"
                    },
                    children=[

            dcc.Tab(
            label="Merging",
            children=[

                html.Br(),

                html.P(
                    "Merging combines several already verified records, single or batch, into one new record with one new signature. This is useful when publishing results that were originally produced as separate runs.", style=TEXT_STYLE
                ),

                html.Hr(),

                tutorial_card(
                    "Step 1: Open the Merge Receipts Tab",
                    [
                        html.P(
                            "Open the Merge Receipts tab.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmMergeTab.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 2: Upload Every Record and Receipt File",
                    [
                        html.P(
                            "Drop in every record and receipt file you want to merge, all into the same box. It does not matter which is which, even files that share the same name (for example several batch_record.json files) are fine, each drop adds to the pile rather than replacing it.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Use Clear files if you want to start over.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmMergeUploadFiles.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 3: Merge and Sign",
                    [
                        html.P(
                            "Click Merge & Sign. Every uploaded record and receipt pair is re-verified first. If any pair fails this check, the merge is refused and nothing is signed.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmMergeButton.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 4: Successful Merge",
                    [
                        html.P(
                            "On success, the tool reports how many source files were combined into how many total LLM requests, plus the new merged_id.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmMergeSuccess.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 5: Merge Refused",
                    [
                        html.P(
                            "If any uploaded record or receipt fails verification, the tool refuses the merge entirely rather than signing a partially untrusted set.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmMergeRefused.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 6: Download the Merged Files",
                    [
                        html.P(
                            "Click Download Merged Record and Download Merged Receipt to get the two files that together make up the new publishable bundle.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmMergeDownload.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

            ]
            ),

            dcc.Tab(
            label="Verification",
            children=[

                html.Br(),

                tutorial_card(
                    "Step 1: Open the Verify Tab",
                    [
                        html.P(
                            "In the LLM Provenance Verification Tool, open the Verify tab.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmVerifyTab.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 2: Upload the Record and Receipt",
                    [
                        html.P(
                            "Drag and drop or click to upload the record file you downloaded from the LLM Provenance Logger (a single record, or a batch_record.json), then do the same for the matching receipt file (or batch_receipt.json) just below it.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmUploadRecord.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 3: Upload the Original Files (Optional)",
                    [
                        html.P(
                            "If the record references any attached files, you may upload them here to additionally check their content. This is Level 2 verification.", style=TEXT_STYLE
                        ),
                        html.P(
                            "Skipping this step still allows Level 1 verification, which checks only the signature against the record.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmUploadFiles.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 4: Download the Public Key",
                    [
                        html.P(
                            "Click Download Public Key if you want to independently verify the signature yourself outside of this tool.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmDownloadPublicKey.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 5: Click Verify",
                    [
                        html.P(
                            "Click Verify to check the uploaded record and receipt.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmVerifyButton.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 6: Successful Verification",
                    [
                        html.P(
                            "If the signature matches and any uploaded files match their recorded hashes, the tool displays a success message describing whether this was a complete Level 2 verification, a Level 1 only verification, or a partial Level 2 verification.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmVerifySuccess.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 7: Failed Verification",
                    [
                        html.P(
                            "If the signature does not match the record, or an uploaded file does not match anything recorded, the tool displays a failure message explaining which check failed.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmVerifyFailure.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

                html.Hr(),

                tutorial_card(
                    "Step 8: Partial Level 2 Verification",
                    [
                        html.P(
                            "If the signature is valid but only some of the referenced files were uploaded, the tool reports a partial Level 2 result, listing how many of the referenced files matched.", style=TEXT_STYLE
                        ),

                        html.Img(
                            src="/assets/llmVerifyPartial.png",
                            style={"width": "100%"}
                        ),
                    ]
                ),

            ]
            ),

                    ]
                ),

                html.Hr(),

                html.H1("Definitions"),

                html.H3("Record"),
                html.P(
                    "A record is the published file containing the prompt, output, model, timestamp, and hash for a single request, or the items array for a batch.", style=TEXT_STYLE
                ),

                html.H3("Receipt"),
                html.P(
                    "The receipt contains the cryptographic signature generated over a record's hash (or, for a batch, over the combined batch hash).", style=TEXT_STYLE
                ),

                html.H3("Level 1 Verification"),
                html.P(
                    "Level 1 checks only that the signature matches the record's hash. It does not require any of the original attached files.", style=TEXT_STYLE
                ),

                html.H3("Level 2 Verification"),
                html.P(
                    "Level 2 additionally checks that uploaded files match the file hashes stored in the record, confirming the original attachments were not swapped.", style=TEXT_STYLE
                ),

                html.H3("Public Key"),
                html.P(
                    "The public key is used to verify that a record's signature was produced by the witness's secret key.", style=TEXT_STYLE
                ),

                html.H3("Merged Record"),
                html.P(
                    "A merged record is a new record combining the LLM requests from several already signed records or batches under one new signature.", style=TEXT_STYLE
                ),

            ]

            )

        ])

    ],

    fluid=True,
    style={
        "fontSize": "20px",
        "maxWidth": "1400px",
        "paddingTop": "30px",
        "paddingBottom": "50px"
    }

)

if __name__ == "__main__":
    app.run(debug=True, port=8053)