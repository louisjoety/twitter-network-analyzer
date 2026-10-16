# RFC-0001: Optional hosted dashboard

Status: draft for discussion. Updated: 17 October 2026.

## Question

If people need access beyond the local computer, how should we host the existing
container while reusing completed analysis results?

## Proposal

Explore one read-only web deployment on Fargate. At startup, the Python service
would retrieve a selected, validated S3 result through a task role. The browser
would continue to use the existing API; users would have no way to launch EMR.
Analysis submission would remain a separate operator action. No database is
proposed for the current fixed dataset.

## Alternatives and trade-offs

| Option | Benefit | Cost or responsibility |
| --- | --- | --- |
| Keep the local Docker app | Smallest setup; existing offline workflow | Access depends on the operator's computer |
| Host the container on Fargate | Avoid managing an operating-system instance | Requires network/access design, service configuration and an ongoing hosting budget |
| Host on EC2 | Direct control over the server | Requires patching, instance lifecycle and recovery work |

## Questions before a decision

Who needs access, and what authentication is appropriate? What hosting budget,
availability expectation and result-refresh policy are acceptable? How will
HTTPS, logs, alerts, health checks and rollback work? Which exact result snapshot
will each deployment use?

This proposal has not been deployed. Record an accepted future decision in a new
ADR and then specify its infrastructure and deployment changes. The current
[ADR](../adr/0001-batch-analysis-and-local-web.md) and [SDD](../SDD.md) describe the
implemented local web application.
