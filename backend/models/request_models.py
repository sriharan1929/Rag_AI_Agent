from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    selected_files: Optional[List[str]] = None
    mode: Optional[str] = "advanced"
    web_search: Optional[bool] = False
    models: Optional[str] = None
    images: Optional[List[str]] = None
