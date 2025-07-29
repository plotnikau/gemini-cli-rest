# Alexa Skill for Gemini REST API

This Alexa skill allows you to interact with a Gemini REST API.

## Installation

### Prerequisites

*   An AWS account.
*   An Amazon Developer account.
*   The ASK CLI installed and configured.
*   A running instance of the Gemini REST API.

### Deployment

1.  **Create the Lambda function:**

    *   Create a new Lambda function in the AWS console.
    *   Choose the Python 3.9 runtime.
    *   Upload the contents of the `lambda_functions` directory as a ZIP file.
    *   Set the handler to `lambda_function.lambda_handler`.

2.  **Configure environment variables:**

    *   `gemini_rest_url`: The URL of your Gemini REST API instance (e.g., `http://<your-ip>:8080`).
    *   `gemini_rest_token`: The authentication token for your Gemini REST API.

3.  **Create the Alexa skill:**

    *   Create a new Alexa skill in the Amazon Developer Console.
    *   Choose the "Custom" model.
    *   Choose the "Provision your own" method.

4.  **Configure the skill:**

    *   **Invocation Name:** Choose a name to invoke the skill (e.g., "Gemini").
    *   **Interaction Model:**
        *   Use the following intent schema:

            ```json
            {
              "intents": [
                {
                  "name": "GptQueryIntent",
                  "slots": [
                    {
                      "name": "query",
                      "type": "AMAZON.SearchQuery"
                    }
                  ],
                  "samples": [
                    "{query}"
                  ]
                },
                {
                  "name": "AMAZON.HelpIntent",
                  "samples": []
                },
                {
                  "name": "AMAZON.CancelIntent",
                  "samples": []
                },
                {
                  "name": "AMAZON.StopIntent",
                  "samples": []
                }
              ]
            }
            ```

    *   **Endpoint:**
        *   Select "AWS Lambda ARN" and enter the ARN of your Lambda function.

    *   **Account Linking:**
        *   Enable account linking.
        *   Choose "Auth Code Grant".
        *   **Authorization URI:** `https://www.amazon.com/ap/oa`
        *   **Access Token URI:** `https://api.amazon.com/auth/o2/token`
        *   **Client ID:** The client ID from your Login with Amazon security profile.
        *   **Client Secret:** The client secret from your Login with Amazon security profile.
        *   **Scope:** `profile`

5.  **Test the skill:**

    *   Use the Alexa simulator in the developer console or a real Alexa device to test the skill.

