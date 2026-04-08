import requests
from models import SQLAction, SQLObservation, StepResult, ResetResult


class SQLQueryEnv:
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def reset(self) -> ResetResult:
        resp = requests.post(f"{self.base_url}/reset", timeout=30)
        resp.raise_for_status()
        return ResetResult(**resp.json())

    def step(self, action: SQLAction) -> StepResult:
        resp = requests.post(
            f"{self.base_url}/step",
            json={"query": action.query},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("observation"):
            data["observation"] = SQLObservation(**data["observation"])
        return StepResult(**data)

    def state(self) -> dict:
        resp = requests.get(f"{self.base_url}/state", timeout=30)
        resp.raise_for_status()
        return resp.json()
