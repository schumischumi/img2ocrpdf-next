from pydantic import BaseModel, HttpUrl

from typing import Sequence

class OcrBase(BaseModel):
    message: str
    status: str

# Properties to return to client
class OcrImage(OcrBase):
    image_path: str
    pass

class OcrBatch(OcrBase):
    batch: bool
    pass