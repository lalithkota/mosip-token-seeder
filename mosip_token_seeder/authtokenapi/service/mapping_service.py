import json

from datetime import datetime
from typing import Union

from sqlalchemy import true
from ..model import MapperFieldIndices, MapperFields, AuthTokenBaseModel

class MappingService:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def validate_auth_data(self, authdata, mapping: Union[MapperFields, MapperFieldIndices], language):
        if isinstance(mapping, MapperFields):
            return self.validate_auth_data_json_mapper(authdata, mapping, language)
        elif isinstance(mapping, MapperFieldIndices):
            return self.validate_auth_data_indices_mapper(authdata, mapping, language)

    def validate_auth_data_json_mapper(self, authdata : dict, mapping: MapperFields, language):
        final_dict = {}
        if mapping.vid not in authdata:
            return None, 'ATS-REQ-009'
        # if len(authdata[mapping.vid]) <= 16 and len(authdata[mapping.vid]) >= 19:
        #     return None, 'ATS-REQ-002'
        final_dict['vid'] = authdata[mapping.vid]

        name_arr = []
        for name_var in mapping.name:
            if name_var in authdata and len(authdata[name_var]) != 0:
                name_arr.append(authdata[name_var])
        if name_arr:
            final_dict['name'] = [{'language':language,'value': self.config.root.name_delimiter.join(name_arr)}]

        if mapping.gender in authdata and len(authdata[mapping.gender]) != 0:
            final_dict['gender'] = [{'language':language,'value': authdata[mapping.gender]}]

        if mapping.dob in authdata and len(authdata[mapping.dob]) != 0:
            final_dict['dob'] = authdata[mapping.dob]
        
        if mapping.phoneNumber in authdata:
            final_dict['phoneNumber'] = authdata[mapping.phoneNumber]

        if mapping.emailId in authdata:
            final_dict['emailId'] = authdata[mapping.emailId]

        addr_arr = []
        for addr in mapping.fullAddress:
            if addr in authdata and len(authdata[addr]) != 0:
                addr_arr.append(authdata[addr])
        if addr_arr:
            final_dict['fullAddress'] = [{'language':language,'value': self.config.root.full_address_delimiter.join(addr_arr)}]

        return AuthTokenBaseModel(**final_dict),""

    def validate_auth_data_indices_mapper(self, authdata : list, mapping: MapperFieldIndices, language):
        final_dict = {}
        len_of_authdata = len(authdata)
        if mapping.vid >= len_of_authdata:
            return None, 'ATS-REQ-009'
        # if len(authdata[mapping.vid]) <= 16 and len(authdata[mapping.vid]) >= 19:
        #     return None, 'ATS-REQ-002'
        final_dict['vid'] = authdata[mapping.vid]

        name_arr = []
        for name_index in mapping.name:
            if name_index >= len_of_authdata:
                return None, 'ATS-REQ-010'
            if len(authdata[name_index]) == 0:
                return None, 'ATS-REQ-003'
            name_arr.append(authdata[name_index])
        final_dict['name'] = [{'language':language,'value': self.config.root.name_delimiter.join(name_arr)}]

        if mapping.gender >= len_of_authdata:
            return None, 'ATS-REQ-011'
        if len(authdata[mapping.gender]) == 0:
            return None, 'ATS-REQ-004'
        # if len(authdata[mapping.gender]) > 256:
        #     return None, 'ATS-REQ-003'
        # if authdata[mapping.gender].lower() not in ['male','female','others']:
        #     return None, 'ATS-REQ-005'
        final_dict['gender'] = [{'language':language,'value': authdata[mapping.gender]}]

        if mapping.dob >= len_of_authdata:
            return None, 'ATS-REQ-012'
        if len(authdata[mapping.dob]) == 0:
            return False, 'ATS-REQ-006'
        # try:
        #     if bool(datetime.strptime(authdata[mapping.dob], '%Y/%m/%d')) == False:
        #         return None, 'ATS-REQ-007'
        # except ValueError:
        #     return None, 'ATS-REQ-007'
        final_dict['dob'] = authdata[mapping.dob]
        
        if mapping.phoneNumber >= len_of_authdata:
            return None, 'ATS-REQ-013'
        final_dict['phoneNumber'] = authdata[mapping.phoneNumber]

        if mapping.emailId >= len_of_authdata:
            return None, 'ATS-REQ-014'
        final_dict['emailId'] = authdata[mapping.emailId]

        addr_arr = []
        for addr_index in mapping.fullAddress:
            if addr_index >= len_of_authdata:
                return None, 'ATS-REQ-015'
            if len(authdata[addr_index]) == 0:
                return False, 'ATS-REQ-008'
            addr_arr.append(authdata[addr_index])
        final_dict['fullAddress'] = [{'language':language,'value': self.config.root.full_address_delimiter.join(addr_arr)}]

        return AuthTokenBaseModel(**final_dict),""
