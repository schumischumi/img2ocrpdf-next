from pydantic import BaseModel, HttpUrl

from typing import Sequence

class OcrBase(BaseModel):
    image_path: str

# Properties to return to client
class Ocr(OcrBase):
    message: str
    status: str
    pass