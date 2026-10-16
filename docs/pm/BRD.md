# BRD: twitter-network-analyzer

Status: current project scope. Updated: 17 October 2026.

## Problem and goals

Repeated relationships in a network file can inflate follower and followee
counts. Users need trustworthy totals and a clear way to find a person's counts
without processing the whole file every time they open the dashboard.

The product should make the results easy to explore, retain evidence of how they
were produced, and let people reuse completed work without paying to repeat it.

## Stakeholder expectations

| Stakeholder | Expected outcome |
| --- | --- |
| Analyst | Accurate counts, lookup by user ID and a browsable list |
| Project owner | Reusable results, controlled processing costs and clear scope |
| Reviewer | Traceable source, test cases and evidence of completed cloud analysis |
| Maintainer | Clear setup, understandable documentation and repeatable checks |

## Success and boundaries

Success means duplicate relationships count once, reference examples match their
expected counts, and users can search and browse completed results without a new
analysis run. The interface supports light and dark themes and clearly identifies
sample data. Technical run details belong in operational records.

The current scope is one supplied network dataset. Live social-media collection,
public accounts, a hosted commercial service and ongoing data refresh are deferred.
No revenue forecast, commercial customer research or response-time SLA is claimed.

See the [PRD](PRD.md) for product requirements and [QA](../qa/README.md) for evidence.
