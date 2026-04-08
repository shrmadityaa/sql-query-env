import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from server.environment import env_reset, env_step, env_state

app = FastAPI(title="SQL Query Environment", version="1.0.0")


class StepInput(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"status": "ok", "env": "sql-query-env", "version": "1.0.0"}


@app.post("/reset")
def reset():
    return env_reset()


@app.post("/step")
def step(inp: StepInput):
    return env_step(inp.query)


@app.get("/state")
def state():
    return env_state()


def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
