# -*- coding: utf-8 -*-
import warnings
import sys

if not sys.warnoptions:
    warnings.filterwarnings("ignore", category=SyntaxWarning)

import os
import logging
import json
import random
import requests
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from datetime import datetime, timezone, timedelta

# Load configurations and localization
def load_config(file_name):
    if str(file_name).endswith(".lang") and not os.path.exists(file_name):
        file_name = "locale/en-US.lang"
    try:
        with open(file_name, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or '=' not in line:
                    continue
                name, value = line.split('=', 1)
                # Store in global vars
                globals()[name] = value
    except Exception as e:
        logger.error(f"Error loading file: {str(e)}")

# Initial config load
load_config("locale/en-US.lang")

# Log configuration
debug = bool(os.environ.get('debug', False))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if debug else logging.INFO)

# Globals for conversation
conversation_id = None
last_interaction_date = None
account_linking_token = None
user_locale = "US"  # Default locale
gemini_rest_url = os.environ.get('gemini_rest_url', "").strip("/")
ask_for_further_commands = bool(os.environ.get('ask_for_further_commands', False))
suppress_greeting = bool(os.environ.get('suppress_greeting', False))

def localize(handler_input):
    # Load locale per user
    locale = handler_input.request_envelope.request.locale
    load_config(f"locale/{locale}.lang")

    # save user_locale var for regional differences in number handling like 2.4°C / 2,4°C
    global user_locale
    user_locale = locale.split("-")[1]  # "de-DE" -> "DE" split to respect lang differencies (not country specific)

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        global conversation_id, last_interaction_date, account_linking_token, suppress_greeting
        
        localize(handler_input)

        # Obtaining Account Linking token
        account_linking_token = handler_input.request_envelope.context.system.user.access_token
        if account_linking_token is None and debug:
            account_linking_token = os.environ.get('gemini_rest_token') # DEBUG Purpose

        # Verifying if token was successfully obtained
        if not account_linking_token:
            logger.error("Unable to get token from Alexa Account Linking or AWS Functions environment variable.")
            speak_output = globals().get("alexa_speak_error")
            return handler_input.response_builder.speak(speak_output).response

        # Sets the last access and defines which welcome phrase to respond to
        now = datetime.now(timezone(timedelta(hours=-3)))
        current_date = now.strftime('%Y-%m-%d')
        speak_output = globals().get("alexa_speak_next_message")
        if last_interaction_date != current_date:
            # First run of the day
            speak_output = globals().get("alexa_speak_welcome_message")
            last_interaction_date = current_date

        if suppress_greeting:
            return handler_input.response_builder.ask("").response
        else:
            return handler_input.response_builder.speak(speak_output).ask(speak_output).response

class GptQueryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        global account_linking_token

        # Ensure locale is set correctly
        localize(handler_input)

        request = handler_input.request_envelope.request
        context = handler_input.request_envelope.context
        response_builder = handler_input.response_builder

        # Get the account linking token
        account_linking_token = context.system.user.access_token

        # Extract user query
        query = request.intent.slots["query"].value
        logger.info(f"Query received from Alexa: {query}")

        # Say processing message while async task runs
        processing_msg = globals().get("alexa_speak_processing")
        response_builder.speak(processing_msg).set_should_end_session(False)

        # Run async call
        response = process_conversation(query)

        logger.debug(f"Ask for further commands enabled: {ask_for_further_commands}")
        if ask_for_further_commands:
            return response_builder.speak(response).ask(globals().get("alexa_speak_question")).response
        else:
            return response_builder.speak(response).set_should_end_session(True).response

# Calls the Gemini REST API and handles the response
def process_conversation(query):
    global conversation_id
    
    # Gets user-configured environment variables
    if not gemini_rest_url:
        logger.error("Please set 'gemini_rest_url' AWS Lambda Functions environment variable.")
        return globals().get("alexa_speak_error")
    
    try:
        headers = {
            "Authorization": "Bearer {}".format(account_linking_token),
            "Content-Type": "application/json",
        }
        data = {
            "prompt": query
        }
        if conversation_id:
            data["conversation_id"] = conversation_id

        gemini_api_url = f"{gemini_rest_url}/chat"
        logger.debug(f"Gemini REST request url: {gemini_api_url}")        
        logger.debug(f"Gemini REST request data: {data}")
        
        response = requests.post(gemini_api_url, headers=headers, json=data)
        
        logger.debug(f"Gemini REST response status: {response.status_code}")
        logger.debug(f"Gemini REST response data: {response.text}")
        
        contenttype = response.headers.get('Content-Type', '')
        logger.debug(f"Content-Type: {contenttype}")
        
        if (contenttype == "application/json"):
            response_data = response.json()
            speech = None

            if response.status_code == 200 and "response" in response_data:
                conversation_id = response_data.get("conversation_id", conversation_id)
                speech = response_data["response"]
            elif "error" in response_data:
                speech = response_data["error"]
                logger.error(f"Error from Gemini REST: {speech}")
            else:
                speech = globals().get("alexa_speak_error")

            if not speech:
                if "message" in response_data:
                    message = response_data["message"]
                    logger.error(f"Empty speech: {message}")
                    return improve_response(f'{globals().get("alexa_speak_error")} {message}')
                else:
                    logger.error(f"Empty speech: {response_data}")
                    return globals().get("alexa_speak_error")

            return improve_response(speech)
        else:
            logger.error(f"Error processing request: {response.text}")
            return globals().get("alexa_speak_error")
            
    except requests.exceptions.Timeout as te:
        logger.error(f"Timeout when communicating with Gemini REST: {str(te)}", exc_info=True)
        return globals().get("alexa_speak_timeout")

    except Exception as e:
        logger.error(f"Error processing response: {str(e)}", exc_info=True)
        return globals().get("alexa_speak_error")

# Replaces words and special characters to improve API response speech
def improve_response(speech):
    global user_locale
    speech = speech.replace(':\n\n', '').replace('\n\n', '. ').replace('\n', ',').replace('-', '').replace('_', ' ')

    # Change decimal separator if user_locale = "de-DE"
    if user_locale == "DE":
        # Only replace decimal separators and not 1.000 separators
        speech = re.sub(r'(\d+)\.(\d{1,3})(?!\d)', r'\1,\2', speech)  # Decimal point (e.g. 2.4 -> 2,4)
    
    return speech

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = globals().get("alexa_speak_help")
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = random.choice(globals().get("alexa_speak_exit").split(";"))
        return handler_input.response_builder.speak(speak_output).set_should_end_session(True).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = globals().get("alexa_speak_error")
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response

sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
lambda_handler = sb.lambda_handler()
