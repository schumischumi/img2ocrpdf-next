from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator
from typing import List, Optional, Union
import os

class Settings(BaseSettings):  # 1
    API_V1_STR: str = "/api/v1"  # 2
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)  # 3
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    if os.environ.get('NEXTCLOUD_URL') is None:
        NEXTCLOUD_URL = 'http://nextcloud.dockerbox.local/'
    else:
        NEXTCLOUD_URL = os.environ['NEXTCLOUD_URL']

    if os.environ.get('NEXTCLOUD_USERNAME') is None:
        NEXTCLOUD_USERNAME = 'none'
    else:
        NEXTCLOUD_USERNAME = os.environ['NEXTCLOUD_USERNAME']

    if os.environ.get('NEXTCLOUD_PASSWORD') is None:
        NEXTCLOUD_PASSWORD = 'none'
    else:
        NEXTCLOUD_PASSWORD = os.environ['NEXTCLOUD_PASSWORD']

    if os.environ.get('NEXTCLOUD_OCR_INPUT_DIR') is None:
        NEXTCLOUD_OCR_INPUT_DIR = '/ocrtest/todo'
    else:
        NEXTCLOUD_OCR_INPUT_DIR = os.environ['NEXTCLOUD_OCR_INPUT_DIR']

    if os.environ.get('NEXTCLOUD_OCR_OUTPUT_DIR') is None:
        NEXTCLOUD_OCR_OUTPUT_DIR = '/ocrtest/done'
    else:
        NEXTCLOUD_USERNEXTCLOUD_OCR_OUTPUT_DIRAME = os.environ['NEXTCLOUD_OCR_OUTPUT_DIR']

    if os.environ.get('NEXTCLOUD_OCR_TAG') is None:
        NEXTCLOUD_OCR_TAG = 'OCR_DONE'
    else:
        NEXTCLOUD_OCR_TAG = os.environ['NEXTCLOUD_OCR_TAG']

    class Config:
        case_sensitive = True  # 4


settings = Settings()  # 5
