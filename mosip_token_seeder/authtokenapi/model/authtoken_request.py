from pydantic import BaseModel, validator
from typing import List, Optional

from ..exception import MOSIPTokenSeederException
from . import MapperFields

supported_output_types = ['json','csv']
supported_delivery_types = ['download','sync']

class AuthTokenBaseRequest(BaseModel):
    print("AuthTokenBaseRequest called")
    deliverytype: str
    output: str
    mapping: MapperFields = MapperFields()
    lang: Optional[str]

    @validator('output', pre=True)
    def output_valid(cls, value, values):
        if values['deliverytype']=='sync':
            return value
        if not value:
            raise MOSIPTokenSeederException('ATS-REQ-102','output type is not mentioned')
        if value not in supported_output_types:
            raise MOSIPTokenSeederException('ATS-REQ-102','output type is not supported')
        return value
    
    @validator('deliverytype', pre=True)
    def delivery_valid(cls, value):
        if not value:
            raise MOSIPTokenSeederException('ATS-REQ-102','delivery type is not mentioned')
        if value not in supported_delivery_types:
            raise MOSIPTokenSeederException('ATS-REQ-102','delivery type is not supported')
        return value

class AuthTokenRequest(AuthTokenBaseRequest):
    authdata: Optional[List[dict]]

    @validator('authdata')
    def auth_data_validate(cls, value):
        if not value:
            raise MOSIPTokenSeederException('ATS-REQ-102','authdata missing')
        return value
