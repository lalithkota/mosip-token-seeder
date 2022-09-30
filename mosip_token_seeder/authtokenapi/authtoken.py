import json
from typing import Optional
from fastapi import Form, UploadFile
from pydantic import Json

from .service import AuthTokenService
from .exception import MOSIPTokenSeederException
from .model import AuthTokenRequest, AuthTokenHttpRequest, AuthTokenCsvHttpRequest, BaseHttpResponse, AuthTokenODKHttpRequest
from .model import AuthTokenHttpRequestSync

class AuthTokenApi:
    def __init__(self, app, config, logger, request_id_queue, authenticator=None):
        self.config = config
        self.logger = logger
        self.authtoken_service = AuthTokenService(config, logger, request_id_queue)
        self.authenticator = authenticator

        if self.config.root.get('sync_operation_mode', False):
            @app.post(config.root.api_path_prefix + "authtoken/json", response_model=BaseHttpResponse, responses={422:{'model': BaseHttpResponse}})
            async def authtoken_json_sync(request : AuthTokenHttpRequestSync = None):
                if not request:
                    raise MOSIPTokenSeederException('ATS-REQ-102', 'mission request body')
                return self.return_auth_token_sync(request.request)
            return

        @app.post(config.root.api_path_prefix + "authtoken/json", response_model=BaseHttpResponse, responses={422:{'model': BaseHttpResponse}})
        async def authtoken_json(request : AuthTokenHttpRequest = None):
            if not request:
                raise MOSIPTokenSeederException('ATS-REQ-102', 'mission request body')
            ##call service to save the details.
            request_identifier = self.authtoken_service.save_authtoken_json(request.request)
            return BaseHttpResponse(response={
                'request_identifier': request_identifier
            })

        @app.post(config.root.api_path_prefix + "authtoken/csv", response_model=BaseHttpResponse, responses={422:{'model': BaseHttpResponse}})
        async def authtoken_csv(request : Json[AuthTokenCsvHttpRequest] = Form(None), csv_file : Optional[UploadFile] = None):
            if not request:
                raise MOSIPTokenSeederException('ATS-REQ-102', 'Missing request body')
            if not csv_file:
                raise MOSIPTokenSeederException('ATS-REQ-102', 'Requires CSV file')
            request_identifier = self.authtoken_service.save_authtoken_csv(request.request, csv_file)
            return BaseHttpResponse(response={
                'request_identifier': request_identifier
            })
        
        @app.post(config.root.api_path_prefix + "authtoken/odk", response_model=BaseHttpResponse, responses={422:{'model': BaseHttpResponse}})
        async def authtoken_odk(request : AuthTokenODKHttpRequest = None):
            request_identifier = self.authtoken_service.save_authtoken_odk(request.request)
            return BaseHttpResponse(response={
                'request_identifier': request_identifier
            })
    def return_auth_token_sync(self, request : AuthTokenRequest):
        if not self.authenticator:
            return BaseHttpResponse(response={
                'message': 'authenticator not found'
            })
        language = request.lang
        if not request.lang:
            language = self.config.root.default_lang_code
        valid_authdata, error_code, error_message = self.authtoken_service.mapping_service.validate_auth_data(
            request.authdata,
            request.mapping,
            language
        )
        if not valid_authdata:
            raise MOSIPTokenSeederException(error_code, error_message)
        else:
            response = json.loads(self.authenticator.do_auth(json.loads(valid_authdata.json())))
            if response and 'response' in response and 'authStatus' in response['response'] and not response['response']['authStatus']:
                if 'authToken' in response['response']:
                    response['response'].pop('authToken')
            if 'errors' in response and response['errors']:
                errors = [{'errorCode': err['errorCode'], 'errorMessage': err['errorMessage']+'. ' + (err['actionMessage'] if 'actionMessage' in err else '')} for err in response['errors']]
                return BaseHttpResponse(errors=errors,response=response['response'])
            else:
                return BaseHttpResponse(response=response['response'])
