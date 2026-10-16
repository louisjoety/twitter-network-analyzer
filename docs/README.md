# Project documentation

Start with the [repository README](../README.md) for a quick overview. Use [setup](setup.md) for installation and run commands.
Paths shown in code blocks are relative to the repository root unless noted.

| Document | What it covers |
| --- | --- |
| [Setup](setup.md) | Native development, Docker and saved-result loading |
| [Cloud evidence](qa/CLOUD-EVIDENCE.md) | Analysis source guide and cloud screenshot locations |
| [Business requirements (BRD)](pm/BRD.md) | Business problem, goals and stakeholder expectations |
| [Product requirements](pm/PRD.md) | Users, scope, functional requirements and acceptance criteria |
| [UX artifacts](ux/README.md) | User flow, wireframe and actual light/dark/mobile screenshots |
| [Software design (SDD)](architecture/SDD.md) | Brief system layout, modules and data flow |
| [Technical specification (TSD)](architecture/TSD.md) | Stack, storage contracts, APIs and deployment behavior |
| [Hosting proposal (RFC-0001)](architecture/rfc/0001-hosted-dashboard.md) | Draft future option, alternatives and open questions |
| [Architecture](architecture/ARCHITECTURE.md) | Components, data flow, API contracts and operating limits |
| [ADR-0001](architecture/adr/0001-batch-analysis-and-local-web.md) | Why the project uses batch Spark, S3 and a local web app |
| [QA plan](qa/README.md) | How to run automated and manual checks |
| [Behavior specs (BDD)](qa/BDD.md) | Given/When/Then scenarios mapped to executable tests |
| [Test cases](qa/TEST-CASES.md) | Inputs, steps and expected outcomes |
| [Test results](qa/TEST-RESULTS.md) | Executed checks and retained cloud evidence |
| [Operations](operations.md) | Startup modes, health checks, troubleshooting and shutdown |
| [Infrastructure guide](../infra/README.md) | Terraform validation and adopting existing S3/EMR resources |
| [Configuration guide](../config/README.md) | Shared example versus private local values |

## How the documents fit

BRD explains why; PRD defines product behavior. RFC proposes a change and ADR
records an accepted decision. SDD gives the design overview; TSD specifies the
implementation contracts. BDD connects observable behavior to executable checks.
The existing architecture document retains the deeper design detail.

## What stays outside docs

Executable source stays in `frontend/`, `backend/` and `analysis/`; executable
regression tests stay in `tests/` and beside frontend components. Terraform source
stays in `infra/` and GitHub workflows stay in `.github/workflows/`.

`runtime/` contains generated, private results and is ignored by Git. It is not
part of the documentation or a required directory in a fresh clone. The separately
retained full-dataset local auditor is not part of this repository's regression suite.
