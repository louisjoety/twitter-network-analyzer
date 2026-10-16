# twitter-network-analyzer

[GitHub](https://github.com/louisjoety/twitter-network-analyzer)

Explore Twitter follower and followee counts with React, Vite, shadcn/ui and a
Python FastAPI backend. PySpark analysis runs on AWS EMR Serverless with S3 input
and output. The dashboard reuses the completed results without rerunning Spark.

## Run locally

With Docker Desktop running and saved results in `runtime/results.json`:

```powershell
docker compose up -d --build --wait
```

Open <http://localhost:8002/>. Stop with `docker compose down`.
For a fresh clone, sample data or native development, see [setup](docs/setup.md).

## Source and documentation

| Area | Location |
| --- | --- |
| Data analysis: cleaning, duplicate removal and counts | [analysis/job.py](analysis/job.py) |
| API and cloud job coordination | [backend/app.py](backend/app.py) |
| Dashboard | [frontend/](frontend/) |
| Cloud execution evidence and screenshot guide | [Cloud evidence](docs/qa/CLOUD-EVIDENCE.md) |
| Tests and expected outcomes | [QA](docs/qa/README.md) |
| Terraform for S3 and EMR | [Infrastructure](infra/README.md) |
| PRD, UX screenshots, architecture and ADR | [Documentation](docs/README.md) |

Local configuration, credentials and saved results are excluded from Git.
