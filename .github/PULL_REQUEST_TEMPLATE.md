## Motivation

<!-- Why is this change needed? Link the issue if there is one. -->

## What changed

<!-- One behaviour per PR. List the concrete changes. -->

## Checklist

- [ ] `pytest -q` passes
- [ ] Report output is byte-identical for the same inputs (golden tests)
- [ ] Finding order deterministic (path, then rule); rule names stable
- [ ] Structural errors stay separate from validation findings
- [ ] If `runtime/` changed: .NET loader semantics match the CLI
- [ ] No new dependencies, no network access
