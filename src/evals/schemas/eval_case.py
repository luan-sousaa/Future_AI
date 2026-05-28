from pydantic import BaseModel, Field
from typing import List, Optional

class EvalMessage(BaseModel):
    role: str
    content: str = ""
    
class EvalCase(BaseModel):
    id: str
    messages: List[EvalMessage]
    
    expected_tools: Optional[List[str]] = Field(default_factory=list)
    expected_keywords: Optional[List[str]] = Field(default_factory=list)
    
    tags: Optional[List[str]] = Field(default_factory=list)
