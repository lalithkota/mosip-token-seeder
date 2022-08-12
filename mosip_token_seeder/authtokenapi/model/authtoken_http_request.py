from datetime import datetime
from pydantic import BaseModel, validator
from typing import List

from ..exception import MOSIPTokenSeederException

from . import AuthTokenRequest

class AuthTokenHttpRequest(BaseModel):
    id: str
    version: str
    metadata: str
    requesttime: datetime
    request: AuthTokenRequest

    @validator('requesttime', pre=True)
    def parse_datetime(cls, value):
        try:
            return datetime.strptime(
                value,
                '%Y-%m-%dT%H:%M:%S.%fZ'
            )
        except:
            # raise MOSIPTokenSeederException('ATS-REQ-102','requesttime is not in valid format')
            return datetime.utcnow()