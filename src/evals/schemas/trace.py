from pydantic import BaseModel  
from typing import List, Dict, Any
from datetime import datetime

class TraceEvent(BaseModel):
    timestamp: str
    type: str
    payload: Dict[str, Any]
    
class ExecutionTrace(BaseModel):
    trace_id: str
    created_at: str
    events: List[TraceEvent]

