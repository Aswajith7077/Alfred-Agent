from typing import Optional
from typing import List
from pydantic import BaseModel


class Image(BaseModel):
    filename: str
    path: str
    size: float
    metadata: Optional[dict] = None


class Document(BaseModel):
    filename: str
    content: str
    filesize: float
    metadata: Optional[dict] = None
    images: Optional[List[Image]] = None
