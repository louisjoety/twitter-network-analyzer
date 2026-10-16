# TSD: twitter-network-analyzer

Status: implemented technical contracts. Updated: 17 October 2026.

## Stack and source

React/TypeScript, Vite, shadcn/ui and Tailwind form the UI. Python 3.12 with
FastAPI/Uvicorn serves the API and production UI build. PySpark runs on EMR
Serverless; S3 stores input and output. Direct dependency versions are in
[Python requirements](../../requirements/base.txt) and [frontend metadata](../../frontend/package.json).

## Input, output and counting rules

Input is a whitespace-separated `src dst` edge list of numeric string IDs:
`src` follows `dst`. Drop repeated complete ordered pairs; preserve reciprocal
pairs and self-loops. Count destinations as followers and sources as followees.
Join both sets of users and fill absent counts with zero.

| Stored object | Contract |
| --- | --- |
| `output/runs/<run>/users/part-*.csv` | Header `user_id,followers,followees`; unique numeric string IDs and nonnegative integer counts |
| `output/runs/<run>/metrics/part-*.json` | One JSON part with row counts, unique edges, users, degree sums, timing and Spark provenance |
| `output/latest.json` | `run_prefix`, `job_run_id`, `completed_at`; published after successful output validation |
| `runtime/results.json` | Local JSON object with `rows` and `metrics`; ignored by Git |

Both degree sums must equal the unique-edge count. The backend rejects incomplete
output, wrong columns, invalid IDs, negative counts, duplicate users and mismatched
totals. Data lives in S3 files and memory; no database schema or migration exists.

## HTTP contracts

| GET endpoint | Success | Errors |
| --- | --- | --- |
| `/api/health` | `status: ready` plus loaded metrics/provenance | Startup must succeed before the service is available |
| `/api/users?offset=0&limit=50` | `items`, `offset`, `limit`, `total`; each item contains `user_id`, `followers`, `followees` | 422 for invalid pagination; offset >= 0, limit 1-200 |
| `/api/users/{user_id}` | One user record | 400 invalid ID; 404 numeric ID absent from the dataset |

Rows are ordered by ID string length, then lexical order. The dashboard
requests 25 users per page. Search and browsing are read-only; no HTTP endpoint
submits a job. Sample mode shows a warning; infrastructure details stay outside
the customer interface. API schemas are also available at `/docs` while running.

## Execution and delivery

`--demo` uses fixtures; `--offline` reads the private cache; default startup reads
saved S3 output. Only explicit `--run-job` submits EMR. Credentials use the AWS
profile/credential chain; configuration defaults to `config/local.json`.

Docker builds React and runs Python as a non-root user. Compose binds port 8002
to localhost and mounts results read-only. CI runs checks without AWS deployment;
image publication is manual. Fargate/EC2 hosting and RDS are future work. See
[setup](../setup.md), [operations](../operations.md), [QA](../qa/README.md) and the
[SDD](SDD.md) for the linked implementation and run instructions.
