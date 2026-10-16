# QA plan

## Scope and approach

Verify graph semantics, data validation, API contracts, job lifecycle safety,
frontend behavior, container startup and infrastructure syntax. Use small graphs
with hand-computed answers and fake AWS clients for regression tests. CI performs
no paid analysis or infrastructure deployment.

| Layer | Tool and location | Verification boundary |
| --- | --- | --- |
| Backend | unittest/FastAPI TestClient, `tests/backend/` | API, S3 result integrity, orchestration and modes; AWS clients are in-memory doubles |
| Analysis | real Spark on tiny graphs, `tests/analysis/` | Production `compute_stats`; Java/PySpark supplied by CI |
| Frontend | Vitest/Testing Library/jsdom, `frontend/src/**/*.test.tsx` | Component interactions and mocked HTTP; not a real-browser end-to-end suite |
| Infrastructure | Terraform fmt/validate, `infra/` | Local syntax/provider schema; no AWS plan/apply |
| Container | Docker build and HTTP smoke check | Built React plus real FastAPI process |
| Cloud evidence | Archived successful job and metrics | One actual completed EMR run; not rerun by tests |
| Browser | Documented manual checks | Layout, real-result rendering and theme persistence |

## Run the automated checks

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests/backend -v
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run lint
```

The analysis suite uses Java 21 and PySpark 4.0.1 in the Linux CI job:

```text
python -m pip install pyspark==4.0.1
python -m unittest discover -s tests/analysis -v
```

For native Windows Spark, use an already working Spark/Java installation with
`SPARK_HOME`, `JAVA_HOME` and `PYSPARK_PYTHON` configured. Windows launcher/native
Hadoop warnings are not test results; require an `OK` summary and exit code zero.
The normal application and backend tests do not need Spark installed locally.

Infrastructure validation, from `infra/`:

```text
terraform fmt -check
terraform init -backend=false -input=false
terraform validate
```

For a fresh-clone Docker smoke test, use `--demo` as documented in [setup](../setup.md).
Real offline Compose testing requires the local `runtime/results.json` cache.

## Entry and exit criteria

Entry: dependencies installed, fixtures available, and no real AWS client used
by regression tests. Each test case lists a specific expected outcome.

Exit: backend, analysis and frontend suites pass; frontend build/lint and
infrastructure validation pass; container is healthy and serves the expected API
payload. Record manual/browser checks and cloud evidence separately. A skipped
Spark suite is not counted as a passed Spark suite.

See [behavior specs](BDD.md), [test cases](TEST-CASES.md) and [execution results](TEST-RESULTS.md). No formal
coverage percentage, security certification, load test or cross-browser pass is
claimed. Public deployment and RDS are outside this release's test scope.
