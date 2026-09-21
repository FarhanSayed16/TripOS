# Incident Report Template

## Incident: [Short Title]
**Date:** YYYY-MM-DD
**Status:** [Investigating / Resolved]
**Severity:** [SEV1 (Platform Down) / SEV2 (Major Feature Degraded) / SEV3 (Minor Issue)]

## Summary
Briefly describe the incident, when it started, and user impact.

## Timeline
- **HH:MM:** Incident detected via [Sentry/User Report/Worker Alert].
- **HH:MM:** Investigation started.
- **HH:MM:** Root cause identified.
- **HH:MM:** Fix deployed.

## Root Cause
Explain what went wrong technically. (e.g., "Supplier API returned unexpected format which caused a KeyError during quote parsing.")

## Resolution
How was the issue fixed? (e.g., "Added a fallback parser in the adapter and deployed hotfix.")

## Action Items (Preventative)
- [ ] Add unit test for this specific edge case.
- [ ] Improve alerting for this failure mode.
