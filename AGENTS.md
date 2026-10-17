# Repository Guidelines

## Project Structure & Module Organization

- `frontend/`: React/TypeScript, Vite, Tailwind and shadcn/ui; components and colocated tests live in `src/`, static assets in `public/`.
- `backend/app.py`: FastAPI endpoints, saved-result loading and explicit EMR coordination. Root `app.py` is the launcher.
- `analysis/job.py`: production PySpark validation, deduplication and aggregation.
- `tests/`: backend/Spark unittest suites, synthetic fixtures and fake AWS clients.
- `infra/`: Terraform and IAM examples. `docs/`: requirements, design, QA and operations.
- `config/`: shared example and private local configuration. Git-ignored `runtime/` stores completed results.

## Build, Test, and Development Commands

Run from the repository root; examples use PowerShell and an existing virtual environment.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/dev.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run dev
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend test
.\.venv\Scripts\python.exe -m unittest discover -s tests/backend -v
```

Vite proxies `/api` to the backend on port 8000. Start it with
`.\.venv\Scripts\python.exe app.py --demo`, or `--offline` for existing real results.
`docker compose up -d --build --wait` serves cached results on localhost:8002;
`docker compose down` stops it. See `docs/setup.md` for prerequisites.

## Coding Style & Naming Conventions

Use four-space Python indentation, `snake_case` functions and descriptive names.
Follow existing TypeScript style: two-space indentation, double quotes, no
semicolons, PascalCase components and camelCase functions. Run Oxlint and the
TypeScript/Vite build; no separate formatter is configured.

## Testing Guidelines

Backend tests use unittest/FastAPI TestClient; frontend tests use Vitest and
Testing Library. Name Python tests `test_*.py`/`test_*` and frontend tests
`*.test.tsx`. Add regression cases for changed behavior; no coverage percentage
is enforced. Spark tests require Java 21/PySpark 4.0.1: run
`python -m unittest discover -s tests/analysis -v` in that environment.

Preserve direction: `src dst` means src follows dst. Deduplicate complete ordered
pairs and retain zero counts. Routine tests use fixtures/fake AWS, never paid jobs.

## Commit & Pull Request Guidelines

History currently contains only `Initial commit`; no commit convention is
established. Use concise imperative subjects, such as `Fix follower count validation`.
Keep changes focused. PRs should explain behavior, link relevant issues, list
validation and include screenshots for UI changes. Update affected documentation.

## Security & Configuration

Never commit credentials, `config/local.json`, raw data, runtime caches or
Terraform state. Use local AWS profiles and `config/example.json`. CI needs no
AWS secrets; manual GHCR publishing uses GitHub's automatic token. Do not submit
EMR jobs or apply/destroy Terraform during routine development or testing.
