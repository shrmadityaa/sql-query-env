
---
title: sql-query-env
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# SQL Query Environment — OpenEnv

A real-world OpenEnv environment where an AI agent learns to write correct SQL
queries of increasing complexity.

## Environment Description

The agent is presented with a natural language question and a database schema.
It must write a SQL query that correctly answers the question. Tasks progress
from easy (simple filtering) to medium (joins) to hard (aggregations).

## Action Space

| Field  | Type   | Description              |
|--------|--------|--------------------------|
| action | string | A valid SQL query string |

## Observation Space

| Field              | Type   | Description                              |
|--------------------|--------|------------------------------------------|
| task_id            | string | Unique task identifier (easy/medium/hard)|
| difficulty         | string | Difficulty level                         |
| question           | string | Natural language question to answer      |
| schema_description | string | Description of the database schema       |

## Reward

- `1.0` — Exact match (all rows correct, no extra rows)
- `0.0–0.9` — Partial F1-based score for partially correct results
- `0.0` — SQL error or completely wrong output

## Tasks

| ID     | Difficulty | Description                                      |
|--------|------------|--------------------------------------------------|
| easy   | easy       | SELECT with WHERE clause                         |
| medium | medium     | JOIN across two tables                           |
| hard   | hard       | GROUP BY + HAVING for aggregation filtering      |

## API

| Endpoint | Method | Description                        |
|----------|--------|------------------------------------|
| `/`      | GET    | Health check                       |
| `/reset` | POST   | Reset environment, get first task  |
| `/step`  | POST   | Submit SQL action, get reward      |
| `/state` | GET    | Get current environment state      |

## Setup

### Local

```bash
pip install -r requirements.txt
uvicorn environment:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t sql-query-env .
docker run -p 7860:7860 sql-query-env
```

### Run Inference

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your-hf-or-openai-key"
export ENV_URL="http://localhost:7860"

python inference.py
```

## Environment Variables

| Variable     | Description                            |
|--------------|----------------------------------------|
| API_BASE_URL | LLM API endpoint                       |
| MODEL_NAME   | Model identifier for inference         |
| HF_TOKEN     | Hugging Face / OpenAI API key          |
| ENV_URL      | Base URL of the running environment    |
