import string
import secrets
import logging
import sys
import traceback

from datetime import datetime

from .model import MOSIPAuthRequest, DemographicsModel, MOSIPEncryptAuthRequest
from .utils import CryptoUtility
from .utils import RestUtility
from .exceptions import AuthenticatorException, Errors

class MOSIPAuthenticator:

    def __init__(self, config_obj, logger=None, **kwargs ):
        if not logger:
            self.logger = self._init_logger(config_obj.logging.log_file_path)
        else:
            self.logger = logger

        self.auth_rest_util = RestUtility(config_obj.mosip_auth_server.ida_auth_url, config_obj.mosip_auth.authorization_header_constant)
        self.crypto_util = CryptoUtility(config_obj.crypto_encrypt, config_obj.crypto_signature)

        self.auth_domain_scheme = config_obj.mosip_auth_server.ida_auth_domain_uri
       
        self.partner_misp_lk =  str(config_obj.mosip_auth.partner_misp_lk)
        self.partner_id = str(config_obj.mosip_auth.partner_id)
        self.partner_apikey = str(config_obj.mosip_auth.partner_apikey)

        self.ida_auth_version = config_obj.mosip_auth.ida_auth_version
        self.ida_auth_request_id = config_obj.mosip_auth.ida_auth_request_id
        self.ida_auth_env = config_obj.mosip_auth.ida_auth_env
        self.timestamp_format = config_obj.mosip_auth.timestamp_format
        self.authorization_header_constant = config_obj.mosip_auth.authorization_header_constant

        self.auth_request = MOSIPAuthRequest(
            id = self.ida_auth_request_id,
            version = self.ida_auth_version,
            env = self.ida_auth_env,
            domainUri = self.auth_domain_scheme,
            specVersion = self.ida_auth_version,
            consentObtained = True,
            metadata = {},
            thumbprint = self.crypto_util.enc_cert_thumbprint,
            individualId = '',
            transactionID = '',
            requestTime = '',
            request = '',
            requestSessionKey = '',
            requestHMAC = '',
        )

    @staticmethod
    def _init_logger(filename):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        fileHandler = logging.FileHandler(filename)
        streamHandler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        fileHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)
        logger.addHandler(fileHandler)
        return logger
    
    def do_auth(self, auth_req_data : dict):
        vid = auth_req_data.pop('vid')
        
        self.logger.info('Received Auth Request.')
        try:
            demographic_data = DemographicsModel(**auth_req_data)
            timestamp = datetime.utcnow()
            timestamp_str = timestamp.strftime(self.timestamp_format) + timestamp.strftime('.%f')[0:4] + 'Z'

            self.auth_request.requestTime = timestamp_str
            self.auth_request.transactionID = ''.join([secrets.choice(string.digits) for _ in range(10)])
            self.auth_request.individualId = vid

            self.auth_request.requestedAuth.demo = True
            
            request = MOSIPEncryptAuthRequest(
                timestamp = timestamp_str,
                biometrics = [],
                demographics = demographic_data
            )
            
            import requests, json
            otp_request = self.auth_request.dict()
            otp_request.pop('request')
            otp_request.pop('requestSessionKey')
            otp_request.pop('requestHMAC')
            otp_request['otpChannel']=['email']
            otp_request['id']='mosip.identity.otp'
            full_request_json = json.dumps(otp_request)

            signature_header = {'Signature': self.crypto_util.sign_auth_request_data(full_request_json)}
            auth_url_backup = str(self.auth_rest_util.auth_server_url)
            self.auth_rest_util.auth_server_url = '/'.join([path if i!=len(auth_url_backup.split('/'))-1 else 'otp' for i, path in enumerate(auth_url_backup.split('/'))])
            path_params = self.partner_misp_lk + '/' + self.partner_id + '/' + self.partner_apikey
            self.logger.info(self.auth_rest_util.post_request(path_params=path_params, data=full_request_json, additional_headers=signature_header).text)
            self.auth_rest_util.auth_server_url = auth_url_backup

            self.auth_request.request, self.auth_request.requestSessionKey, self.auth_request.requestHMAC = \
                    self.crypto_util.encrypt_auth_data(json.dumps({"otp":input('Enter the otp received: '), "timestamp": timestamp_str }))
            self.auth_request.id = 'mosip.identity.kyc'
            full_request_json = self.auth_request.json()

            signature_header = {'Signature': self.crypto_util.sign_auth_request_data(full_request_json)}

            path_params = self.partner_misp_lk + '/' + self.partner_id + '/' + self.partner_apikey
            response = self.auth_rest_util.post_request(path_params=path_params, data=full_request_json, additional_headers=signature_header)
            self.logger.info('Auth Request Processed Completed.')
            
            return response.text
        except:
            exp = traceback.format_exc()
            self.logger.error('Error Processing Auth Request. Error Message: {}'.format(exp))
            raise AuthenticatorException(Errors.AUT_BAS_001.name, Errors.AUT_BAS_001.value)
        
