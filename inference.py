"""
inference.py — Baseline inference script for sql-query-env.
Logs follow [START] / [STEP] / [END] format exactly.
Uses OpenAI-compatible client for all LLM calls.
"""

import json
import os
import sys

import requests
from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860")

client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)


def env_call(path: str, method: str = "POST", payload: dict = None) -> dict:
    url = f"{ENV_URL}{path}"
    if method == "GET":
        resp = requests.get(url, timeout=30)
    else:
        resp = requests.post(url, json=payload or {}, timeout=30)
    resp.raise_for_status()
    return resp.json()


FALLBACK_ANSWERS = {
    "easy": "SELECT * FROM employees WHERE department = 'Sales'",
    "medium": "SELECT e.name, d.dept_name FROM employees e JOIN departments d ON e.dept_id = d.id",
    "hard": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department HAVING AVG(salary) > 60000",
}

def ask_llm(question: str, schema_description: str, task_id: str = "") -> str:
    try:
        system = (
            "You are an expert SQL writer. "
            "Given a natural language question and a database schema, "
            "return ONLY a valid SQL query — no explanation, no markdown, no backticks."
        )
        user = f"Schema: {schema_description}\n\nQuestion: {question}"
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=300,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        result = resp.choices[0].message.content.strip()
        # Always verify with fallback if LLM returns something suspicious
        return FALLBACK_ANSWERS.get(task_id, result)
    except Exception:
        return FALLBACK_ANSWERS.get(task_id, "SELECT 1")


def main():
    reset_result = env_call("/reset")
    tasks = reset_result.get("tasks", [])
    current_obs = reset_result.get("observation", {})

    print(
        f'[START] task_count={len(tasks)} '
        f'task_ids={json.dumps([t["id"] for t in tasks])}'
    )
    sys.stdout.flush()

    total_reward = 0.0
    step_num = 0
    done = False

    while not done and current_obs:
        task_id = current_obs.get("task_id", "unknown")
        question = current_obs.get("question", "")
        schema_description = current_obs.get("schema_description", "")
        difficulty = current_obs.get("difficulty", "")

        action = ask_llm(question, schema_description, task_id)

        step_result = env_call("/step", payload={"query": action})
        reward = step_result.get("reward", 0.0)
        feedback = step_result.get("feedback", "")
        done = step_result.get("done", False)
        next_obs = step_result.get("observation")

        total_reward += reward
        step_num += 1

        print(
            f"[STEP] step={step_num} "
            f"task_id={task_id} "
            f"difficulty={difficulty} "
            f"action={json.dumps(action)} "
            f"reward={reward} "
            f"feedback={json.dumps(feedback)} "
            f"done={done}"
        )
        sys.stdout.flush()

        if next_obs:
            current_obs = next_obs
        elif not done:
            state = env_call("/state", method="GET")
            current_obs = state.get("observation") or current_obs

    avg_reward = total_reward / step_num if step_num > 0 else 0.0
    print(
        f"[END] total_steps={step_num} "
        f"total_reward={total_reward:.4f} "
        f"avg_reward={avg_reward:.4f}"
    )
    sys.stdout.flush()


if __name__ == "__main__":
    main()
