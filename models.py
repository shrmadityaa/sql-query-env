from pydantic import BaseModel
from typing import Optional


class SQLAction(BaseModel):
    query: str  # The SQL query string the agent submits


class SQLObservation(BaseModel):
    task_id: str
    difficulty: str  # easy | medium | hard
    question: str
    schema_description: str


class StepResult(BaseModel):
    observation: Optional[SQLObservation]
    reward: float
    done: bool
    feedback: str


class ResetResult(BaseModel):
    observation: SQLObservation
    tasks: list[dict]
    message: str
