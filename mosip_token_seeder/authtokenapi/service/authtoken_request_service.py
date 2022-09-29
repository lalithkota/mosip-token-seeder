import codecs
import csv
import json
import logging
from typing import List, Union
import uuid

from datetime import date, datetime
from webbrowser import get

from fastapi import UploadFile

from mosip_token_seeder.authtokenapi.model.authtoken_odk_request import AuthTokenODKRequest
from mosip_token_seeder.authtokenapi.service.odk_pull_service import ODKPullService

from ..model import AuthTokenRequest
from ..model import AuthTokenCsvRequestWithHeader
from ..exception import MOSIPTokenSeederNoException
from mosip_token_seeder.repository import AuthTokenRequestRepository, AuthTokenRequestDataRepository
from mosip_token_seeder.repository import db_tools
from . import MappingService


class AuthTokenService:
    def __init__(self, config, logger, request_id_queue):
        self.mapping_service = MappingService(config, logger)
        self.config = config
        self.db_engine = db_tools.db_init(
            config.db.location, password=config.db.password)
        self.logger = logger
        self.request_id_queue = request_id_queue

    def save_authtoken_json(self, request: AuthTokenRequest):

        language = request.lang
        if not request.lang:
            language = self.config.root.default_lang_code

        req_id = self.get_new_req_id()

        authtoken_request_entry = AuthTokenRequestRepository(
            auth_request_id=req_id,
            number_total=len(request.authdata),
            input_type='json',
            output_type=request.output,
            delivery_type=request.deliverytype,
            status='submitted'
        )

        line_no = 0
        error_count = 0
        for authdata in request.authdata:
            line_no += 1
            authdata_model = AuthTokenRequestDataRepository(
                auth_request_id=req_id,
                auth_request_line_no=line_no,
                auth_data_received=json.dumps(authdata),
            )
            valid_authdata, error_code, error_message= self.mapping_service.validate_auth_data(
                authdata, request.mapping, language)
            if valid_authdata:
                authdata_model.auth_data_input = valid_authdata.json()
                authdata_model.status = 'submitted'
            else:
                error_count += 1
                authdata_model.status = 'invalid'
                authdata_model.error_code = error_code
                authdata_model.error_message = error_message
            authdata_model.add(self.db_engine)

        authtoken_request_entry.number_error = error_count

        if(error_count == line_no):
            authtoken_request_entry.status = 'submitted_with_errors'
            authtoken_request_entry.add(self.db_engine)
            self.request_id_queue.put(req_id)
            raise MOSIPTokenSeederNoException('ATS-REQ-101', 'none of the record form a valid request', 200, response={
                'request_identifier': req_id
            })

        authtoken_request_entry.add(self.db_engine)
        self.request_id_queue.put(req_id)
        return req_id

    def save_authtoken_csv(self, request: AuthTokenCsvRequestWithHeader, csv_file: UploadFile):
        language = request.lang
        if not request.lang:
            language = self.config.root.default_lang_code

        req_id = self.get_new_req_id()

        csv_header = None

        line_no = 0
        error_count = 0
        csv_reader = csv.reader(codecs.iterdecode(
            csv_file.file, 'UTF-8'), delimiter=request.csvDelimiter)
        for csv_line in csv_reader:
            if not csv_header:
                csv_header = csv_line
                continue

            len_csv_line = len(csv_line)

            authdata = {column_name: csv_line[i] if i < len_csv_line else None
                        for i, column_name in enumerate(csv_header)}

            line_no += 1

            authdata_model = AuthTokenRequestDataRepository(
                auth_request_id=req_id,
                auth_request_line_no=line_no,
                auth_data_received=json.dumps(authdata),
            )
            valid_authdata, error_code, error_message = self.mapping_service.validate_auth_data(
                authdata, request.mapping, language)
            if valid_authdata:
                authdata_model.auth_data_input = valid_authdata.json()
                authdata_model.status = 'submitted'
            else:
                error_count += 1
                authdata_model.status = 'invalid'
                authdata_model.error_code = error_code
                authdata_model.error_message = error_message
            authdata_model.add(self.db_engine)

        authtoken_request_entry = AuthTokenRequestRepository(
            auth_request_id=req_id,
            number_total=line_no,
            input_type='csv',
            output_type=request.output,
            delivery_type=request.deliverytype,
            status='submitted',
            number_error=error_count,
        )

        if(error_count == line_no):
            authtoken_request_entry.status = 'submitted_with_errors'
            authtoken_request_entry.add(self.db_engine)
            self.request_id_queue.put(req_id)
            raise MOSIPTokenSeederNoException('ATS-REQ-101', 'none of the record form a valid request', 200, response={
                'request_identifier': req_id
            })

        authtoken_request_entry.add(self.db_engine)
        self.request_id_queue.put(req_id)
        return req_id

    def save_authtoken_odk(self, request: AuthTokenODKRequest):

        odk_pull_service = ODKPullService(self.logger)
        auth_request_data = odk_pull_service.odk_pull(request.odkconfig)
        language = request.lang
        if not request.lang:
            language = self.config.root.default_lang_code

        req_id = self.get_new_req_id()

        authtoken_request_entry = AuthTokenRequestRepository(
            auth_request_id=req_id,
            number_total=len(auth_request_data),
            input_type='json',
            output_type=request.output,
            delivery_type=request.deliverytype,
            status='submitted'
        )

        line_no = 0
        error_count = 0
        for authdata in auth_request_data:
            line_no += 1
            authdata_model = AuthTokenRequestDataRepository(
                auth_request_id=req_id,
                auth_request_line_no=line_no,
                auth_data_received=json.dumps(authdata),
            )
            valid_authdata, error_code, error_message = self.mapping_service.validate_auth_data(
                authdata, request.mapping, language)
            if valid_authdata:
                authdata_model.auth_data_input = valid_authdata.json()
                authdata_model.status = 'submitted'
            else:
                error_count += 1
                authdata_model.status = 'invalid'
                authdata_model.error_code = error_code
                authdata_model.error_message = error_message
            authdata_model.add(self.db_engine)

        authtoken_request_entry.number_error = error_count

        if(error_count == line_no):
            authtoken_request_entry.status = 'submitted_with_errors'
            authtoken_request_entry.add(self.db_engine)
            self.request_id_queue.put(req_id)
            raise MOSIPTokenSeederNoException('ATS-REQ-101', 'none of the record form a valid request', 200, response={
                'request_identifier': req_id
            })

        authtoken_request_entry.add(self.db_engine)
        self.request_id_queue.put(req_id)
        return req_id

    def fetch_status(self, request_identifier):

        try:
            status = AuthTokenRequestRepository.fetch_status(
                request_identifier, self.db_engine)
        except Exception as e:
            raise MOSIPTokenSeederNoException(
                'ATS-REQ-016', 'no auth request found for the given identifier', 404)
        if not status:
            raise MOSIPTokenSeederNoException(
                'ATS-REQ-016', 'no auth request found for the given identifier', 404)
        return status

    def assert_download_status(self, request_identifier):
        status = self.fetch_status(request_identifier)
        if not status.startswith('processed'):
            raise MOSIPTokenSeederNoException(
                'ATS-REQ-017', 'Auth request not processed yet', 202)

    def get_new_req_id(self):
        return f'{self.config.docker.pod_id:02}' + str(uuid.uuid4())[2:]
