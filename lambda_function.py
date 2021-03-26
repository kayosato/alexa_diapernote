
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response, DialogState

from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model.dialog_state import DialogState

from datetime import datetime



# LINE
import requests
from ask_sdk_core.utils import get_api_access_token

LINE_API_BASE_URL = 'https://api.line.me/v2'
MESSAGING_API_ACCESSTOKEN = '## Input messaging api accesstoken ##'


# S3PersistenceAdapterを用意
import os
import boto3
from ask_sdk_s3.adapter import S3Adapter
from ask_sdk_core.skill_builder import CustomSkillBuilder

# ask persistence adapterの読み込み
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

# 永続性アダプターを初期化
## S3
bucket_region = os.environ.get('S3_PERSISTENCE_REGION')
bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')

s3_client = boto3.client('s3', region_name = bucket_region)
s3_adapter = S3Adapter(bucket_name, s3_client = s3_client)

## DynamoDB
ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME')

ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)


import line_function

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):

        speak_output = "おむつメモです。取り替えたおむつは何グラムですか？種類と重さを言ってください。"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class DiapersNoteIntentHandler(AbstractRequestHandler):
    """Handler for Diapers Note Intent."""
    def can_handle(self, handler_input):

        return ask_utils.is_intent_name("DiapersNoteIntent")(handler_input)


    def handle(self, handler_input):
        
        session_attr = handler_input.attributes_manager.session_attributes

        pee_poo = get_slot_value(handler_input=handler_input, slot_name="pee_poo")
        total = get_slot_value(handler_input=handler_input, slot_name="weight")
        
        persistence_attr = handler_input.attributes_manager.persistent_attributes
        diaper = persistence_attr['diaper']
        
        if diaper.isdigit() :
            
            profile_access_token = handler_input.request_envelope.context.system.user.access_token
            resBody = line_function.get_profile(LINE_API_BASE_URL, profile_access_token)
            userId = resBody["userId"]
            
            delta = int(total) - int(diaper)
            
            message = ("{0}が{1}グラム出ました。元の重さ：{2}グラム。おむつのみの重さ：{3}グラム。".format(pee_poo, delta, total, diaper))
            
            resBody = line_function.push(userId, message, LINE_API_BASE_URL, MESSAGING_API_ACCESSTOKEN)
            
            
            if str(resBody)[0] == '4' or str(resBody)[0] == '5':
                speak_output = ("メッセージを送信できませんでした。エラーコードは{}です。".format(resBody))
            else:
                speak_output = ("おむつの重さを{0}グラムで計算します。{1}を{2}グラムで通知します。".format(diaper, pee_poo, delta))
            
        else:
            speak_output = ("おむつだけの重さが未登録です。おむつを何グラムで登録してと言って重量を登録してください。")
        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class InitialDiaperIntentHandler(AbstractRequestHandler):
    """Handler for Diapers Note Intent."""
    def can_handle(self, handler_input):

        return ask_utils.is_intent_name("InitialDiaperIntent")(handler_input)


    def handle(self, handler_input):

        diaper_weight = get_slot_value(handler_input=handler_input, slot_name="diaper")

        persistence_attr = handler_input.attributes_manager.persistent_attributes
        persistence_attr['diaper'] = diaper_weight
        
        handler_input.attributes_manager.save_persistent_attributes()

        
        session_attr = handler_input.attributes_manager.session_attributes

        if not session_attr:
            speak_output = "おむつの重さを" + diaper_weight + "グラムで登録します。"
            
        else:
            pee_poo_session = session_attr["pee_poo"]
            totalweight_session = session_attr["totalweight"]
            
            delta = int(totalweight_session) - int(diaper_weight)
            speak_output = ("おむつの重さを{0}グラムで計算します。{1}を{2}グラムでメモします。".format(diaper_weight, pee_poo_session, delta))
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )



class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "バイバイ!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response



class IntentReflectorHandler(AbstractRequestHandler):

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = intent_name + "というインテントが呼ばれました。"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "すみません、何か上手くいかないみたいです。もう一度試してください。"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


sb = SkillBuilder()

#sb = CustomSkillBuilder(persistence_adapter = s3_adapter)
sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(DiapersNoteIntentHandler())
sb.add_request_handler(InitialDiaperIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()