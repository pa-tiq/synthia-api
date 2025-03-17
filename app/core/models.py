from pydantic import BaseModel
from app.core.enums import FileType


class SummaryResponse(BaseModel):
    summary: str
    file_type: FileType
    file_name: str
