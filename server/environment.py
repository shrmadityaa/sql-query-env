import sqlite3
from typing import Optional

TASKS = [
    {
        "id": "easy",
        "difficulty": "easy",
        "question": "Write a SQL query to retrieve all employees who work in the 'Sales' department.",
        "schema_description": (
            "Table: employees(id INTEGER, name TEXT, department TEXT, salary REAL). "
            "Rows: (1,'Alice','Sales',60000), (2,'Bob','Engineering',90000), (3,'Carol','Sales',55000)"
        ),
        "schema_sql": """
            CREATE TABLE employees (id INTEGER, name TEXT, department TEXT, salary REAL);
            INSERT INTO employees VALUES (1,'Alice','Sales',60000);
            INSERT INTO employees VALUES (2,'Bob','Engineering',90000);
            INSERT INTO employees VALUES (3,'Carol','Sales',55000);
        """,
        "expected": {(1, "Alice", "Sales", 60000.0), (3, "Carol", "Sales", 55000.0)},
    },
    {
        "id": "medium",
        "difficulty": "medium",
        "question": (
            "Write a SQL query to get each employee's name and their department name "
            "by joining the employees and departments tables."
        ),
        "schema_description": (
            "Table: employees(id INTEGER, name TEXT, dept_id INTEGER, salary REAL). "
            "Table: departments(id INTEGER, dept_name TEXT). "
            "employees.dept_id references departments.id."
        ),
        "schema_sql": """
            CREATE TABLE employees (id INTEGER, name TEXT, dept_id INTEGER, salary REAL);
            CREATE TABLE departments (id INTEGER, dept_name TEXT);
            INSERT INTO employees VALUES (1,'Alice',1,60000);
            INSERT INTO employees VALUES (2,'Bob',2,90000);
            INSERT INTO employees VALUES (3,'Carol',1,55000);
            INSERT INTO departments VALUES (1,'Sales');
            INSERT INTO departments VALUES (2,'Engineering');
        """,
        "expected": {("Alice", "Sales"), ("Bob", "Engineering"), ("Carol", "Sales")},
    },
    {
        "id": "hard",
        "difficulty": "hard",
        "question": (
            "Write a SQL query to find each department and its average salary, "
            "but only include departments where the average salary is above 60000. "
            "Return columns: department, avg_salary."
        ),
        "schema_description": (
            "Table: employees(id INTEGER, name TEXT, department TEXT, salary REAL). "
            "Rows include Sales(avg~57500), Engineering(avg=87500), HR(avg=50000)."
        ),
        "schema_sql": """
            CREATE TABLE employees (id INTEGER, name TEXT, department TEXT, salary REAL);
            INSERT INTO employees VALUES (1,'Alice','Sales',60000);
            INSERT INTO employees VALUES (2,'Bob','Engineering',90000);
            INSERT INTO employees VALUES (3,'Carol','Sales',55000);
            INSERT INTO employees VALUES (4,'Dave','Engineering',85000);
            INSERT INTO employees VALUES (5,'Eve','HR',50000);
        """,
        "expected": {("Engineering", 87500.0)},
    },
]

_state = {
    "task_index": 0,
    "current_task": None,
    "done": False,
    "last_reward": 0.0,
    "step_count": 0,
    "total_reward": 0.0,
}


def _observation(task: dict) -> dict:
    return {
        "task_id": task["id"],
        "difficulty": task["difficulty"],
        "question": task["question"],
        "schema_description": task["schema_description"],
    }


def _run_sql(schema_sql: str, query: str):
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_sql)
        cur = conn.execute(query)
        rows = cur.fetchall()
        return rows, None
    except Exception as exc:
        return None, str(exc)
    finally:
        conn.close()


def _grade(task: dict, query: str) -> tuple[float, str]:
    rows, error = _run_sql(task["schema_sql"], query)
    if error:
        return 0.01, f"SQL error: {error}"

    result_set = set(tuple(r) for r in rows)
    expected = task["expected"]

    if result_set == expected:
        return 0.99, "Perfect match — all rows correct."

    correct = len(result_set & expected)
    extra = len(result_set - expected)
    missing = len(expected - result_set)

    if correct == 0:
        return 0.01, f"No matching rows. Missing {missing}, got {len(result_set)} wrong rows."

    precision = correct / (correct + extra) if (correct + extra) > 0 else 0
    recall = correct / len(expected)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return max(0.01, round(f1 * 0.9, 4)), f"Partial: {correct}/{len(expected)} correct rows, {extra} extra."


def env_reset() -> dict:
    _state["task_index"] = 0
    _state["current_task"] = TASKS[0]
    _state["done"] = False
    _state["last_reward"] = 0.0
    _state["step_count"] = 0
    _state["total_reward"] = 0.0
    return {
        "observation": _observation(TASKS[0]),
        "tasks": [{"id": t["id"], "difficulty": t["difficulty"]} for t in TASKS],
        "message": "Environment reset. Solve 3 SQL tasks of increasing difficulty.",
    }


def env_step(query: str) -> dict:
    task = _state["current_task"]
    if task is None or _state["done"]:
        return {"reward": 0.0, "feedback": "Call /reset first.", "done": True, "observation": None}

    reward, feedback = _grade(task, query)
    _state["last_reward"] = reward
    _state["total_reward"] += reward
    _state["step_count"] += 1

    advance = reward >= 0.5 or _state["step_count"] >= 3
    next_obs = None
    done = False

    if advance:
        _state["task_index"] += 1
        _state["step_count"] = 0
        if _state["task_index"] >= len(TASKS):
            done = True
            _state["done"] = True
            _state["current_task"] = None
        else:
            _state["current_task"] = TASKS[_state["task_index"]]
            next_obs = _observation(_state["current_task"])

    return {"reward": reward, "feedback": feedback, "done": done, "observation": next_obs}


def env_state() -> dict:
    task = _state["current_task"]
    return {
        "task_index": _state["task_index"],
        "current_task_id": task["id"] if task else None,
        "done": _state["done"],
        "last_reward": _state["last_reward"],
        "total_reward": _state["total_reward"],
        "step_count": _state["step_count"],
        "observation": _observation(task) if task else None,
    }
