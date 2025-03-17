from pydantic import BaseModel
from enum import Enum
from app.core.enums import FileType


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SummaryResponse(BaseModel):
    summary: str
    file_type: FileType
    file_name: str


class JobStatusResponse(BaseModel):
    status: JobStatus
    job_id: str
    summary: str | None = None
    error: str | None = None
