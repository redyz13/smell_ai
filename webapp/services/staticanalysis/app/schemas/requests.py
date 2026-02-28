from pydantic import BaseModel
from typing import List, Optional

class FilePayload(BaseModel):
    filename: str
    content: str

class DetectSmellRequest(BaseModel):
    """
    Schema for the request body to detect code smells.
    """
    # Manteniamo il code_snippet per retrocompatibilità, ma aggiungiamo la lista di file
    code_snippet: Optional[str] = None
    files: Optional[List[FilePayload]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "files": [{"filename": "main.py", "content": "print('Hello, world!')"}]
            }
        }