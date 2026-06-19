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
            label="Verification Tutorial",

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