# ADR-0001: Batch Spark analysis, S3 results and a local web app

Date: 17 October 2026. Status: accepted for the project prototype.

## Context

The application requires a full-stack application and distributed analysis of a fixed
Twitter dataset with duplicates. The implementation must demonstrate real cloud
execution, expose counts through APIs and avoid unnecessary operating cost or
infrastructure management. The selected stack is React/Vite/shadcn and Python.

## Decision

Use EMR Serverless for explicitly submitted PySpark batch jobs and private S3 for
input, scripts, immutable run output and logs. FastAPI coordinates jobs, validates
aggregates and serves the React build. Keep the web app on the laptop, with a
saved-results mode for later demonstrations. Package it as one container.

Deduplicate complete ordered `(src, dst)` pairs before aggregation. Preserve
reciprocal pairs, exact string IDs, one-sided users and self-loops. Publish a new
"latest" pointer only after success and validated result retrieval.

Store infrastructure definitions under `infra/`; keep CI read-only with respect
to AWS. Publish container images only through a manually triggered workflow.

## Alternatives considered

| Alternative | Assessment |
| --- | --- |
| Managed EC2 cluster for every demonstration | Adds server lifecycle and idle-capacity management to this small project |
| Entire pipeline on the laptop | Useful for separate verification, but does not provide the chosen cloud execution evidence |
| Fargate/EC2 hosting plus RDS now | Adds persistent hosting, network, access and schema work without improving the fixed-dataset requirement |
| Recompute on each search | Adds latency and repeated compute charges; batch aggregates already answer the queries |

## Consequences

The solution is small, reproducible and usable after the cloud run without
repeating it. Cold startup adds time to the first EMR job. Results are snapshots
and the backend holds aggregate data in memory; this is not a streaming or
multi-tenant service. Local caches are private runtime data, not repository files.

Public hosting requires a follow-up access/network/deployment decision. A large
or frequently updated dataset may justify a database and refresh policy later.
This ADR does not claim that those future services have been deployed.
