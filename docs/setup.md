# Setup and development

Use Python 3.12 and Node 24. Run commands from the repository root.

## Native Python and React

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/base.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe app.py --demo
```

Open <http://localhost:8000/>. Demo mode uses five synthetic users (100-500) and
shows a sample warning. Java and Spark are not needed for the web app.

For real results already on this computer, use `app.py --offline` instead. The
cache is `runtime/results.json`; it is private and excluded from Git. A fresh clone
needs its own cache or access to an existing completed S3 result.

For development, install `requirements/dev.txt` instead of `base.txt`; it includes
the application dependencies and adds backend test tools. Keep the backend on
port 8000 and run `npm.cmd --prefix frontend run dev` in another terminal. Vite
proxies `/api` to FastAPI. Build again before serving frontend changes via FastAPI.
See [QA](qa/README.md) for tests and separate Java/PySpark prerequisites.

## Docker

With a real cache in `runtime/results.json`:

```powershell
docker compose up -d --build --wait
docker compose ps
```

Open <http://localhost:8002/>. Compose mounts the cache read-only and starts
`--offline`. Stop with `docker compose down`; the host cache remains intact.

Without a real cache, build and run the labelled sample:

```powershell
docker build -t twitter-network-analyzer:local .
docker run --rm -p 127.0.0.1:8002:8000 twitter-network-analyzer:local --demo
```

The image builds React and serves it through a non-root Python process. It has a
health check and excludes credentials, private configuration and cached output.

## Load existing S3 results

Create `config/local.json` using the [configuration guide](../config/README.md),
then use your existing AWS CLI profile:

```powershell
.\.venv\Scripts\python.exe app.py --profile your-profile
```

This reads the completed S3 output and saves the offline cache. A new analysis is
submitted only with the explicit `--run-job` flag. Existing output is sufficient
for this project's demonstrations. See [operations](operations.md) for startup
modes, troubleshooting and shutdown, and [infrastructure](../infra/README.md) for
Terraform validation and existing-resource imports.

Keep credentials, `config/local.json`, raw data, `runtime/`, dependencies, build
output and Terraform state out of Git. Commit the npm and Terraform lockfiles.
