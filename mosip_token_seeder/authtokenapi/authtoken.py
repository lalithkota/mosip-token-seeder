import json
from typing import Optional
from fastapi import File, Form, Request, UploadFile, Response
from pydantic import Json

from mosip_token_seeder.repository import db_tools

from .service import AuthTokenService
from .exception import MOSIPTokenSeederException
from .model import AuthTokenRequest, AuthTokenHttpRequest, AuthTokenCsvHttpRequest, BaseHttpResponse, AuthTokenODKHttpRequest

class AuthTokenApi:
    def __init__(self, app, config, logger, request_id_queue, authenticator=None):
        self.config = config
        self.logger = logger
        self.authtoken_service = AuthTokenService(config, logger, request_id_queue)
        self.authenticator = authenticator

        @app.post(config.root.api_path_prefix + "authtoken/json", response_model=BaseHttpResponse, responses={422:{'model': BaseHttpResponse}})
        async def authtoken_json(request : AuthTokenHttpRequest = None):
            if not request:
                raise MOSIPTokenSeederException('ATS-REQ-102', 'mission request body')
            ##call service to save the details.
            if request.request.deliverytype=='sync':
                return Response(self.returnAuthTokenSync(request.request), media_type="application/json")
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
            # test = AuthTokenODKHttpRequest()
            # print(json.dumps(request))
            # if not request:
            #     raise MOSIPTokenSeederException('ATS-REQ-102', 'Missing request body.')
           
            request_identifier = self.authtoken_service.save_authtoken_odk(request.request)
            return BaseHttpResponse(response={
                'request_identifier': request_identifier
            })
    
    def returnAuthTokenSync(self, request : AuthTokenRequest):
        if not self.authenticator:
            return BaseHttpResponse(response={
                'message': 'authenticator not found'
            })
        language = request.lang
        if not request.lang:
            language = self.config.root.default_lang_code
        valid_authdata, error_code = self.authtoken_service.mapping_service.validate_auth_data(
            request.authdata[0],
            request.mapping,
            language
        )
        if not valid_authdata:
            raise MOSIPTokenSeederException(error_code, '')
        else:
            return self.authenticator.do_auth(json.loads(valid_authdata.json()))