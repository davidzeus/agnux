from pydantic import BaseModel
from typing import Literal, Dict, Any, List, Optional

class TaskbarPrompt(BaseModel):
    prompt: str
    user_id: str
    terminal_id: str

class EnrolmentPayload(BaseModel):
    enrolment_id: str
    facial_matrix: list[float]
    vocal_matrix: list[float]

class LinkTerminalPayload(BaseModel):
    user_id: str
    terminal_id: str

class BiometricLoginPayload(BaseModel):
    terminal_id: str
    matrix: list[float]
