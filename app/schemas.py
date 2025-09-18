from pydantic import BaseModel, Field
from typing import Optional, Any

class EventIn(BaseModel):
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    node: Optional[str] = None
    error_message: str = Field(..., min_length=1)
    error_stack: Optional[str] = None
    run_id: Optional[str] = None
    attempt: Optional[int] = 0
    payload: Optional[Any] = None
