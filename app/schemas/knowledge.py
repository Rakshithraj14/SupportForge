from pydantic import BaseModel


class KnowledgeUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    chunk_count: int | None = None
