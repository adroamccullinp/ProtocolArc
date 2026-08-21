# Contributing to ProtocolArc

Thanks for helping make agent message shapes explicit and versioned.

## Ground rules

- **Stdlib Python + optional .NET.** The CLI is Python 3 standard library
  only. The `runtime/` loader targets .NET 9 and must mirror CLI semantics
  exactly. No third-party dependencies on either side.
- **Deterministic findings.** Findings are ordered (path, then rule) and
  rule names are machine-stable. Same inputs, byte-identical report.
- **Errors are not findings.** A malformed document raises a structural
  error; a well-formed non-conforming envelope produces findings. Never mix
  the two.

## Workflow

1. Branch from `main` (`feat/<topic>` or `fix/<topic>`).
2. One behaviour per PR - small and reviewable.
3. Check locally:
   ```bash
   pip install -e .
   pytest
   python -m protocolarc diff examples/contracts/mcp_tool_call_1.0.0.json examples/contracts/mcp_tool_call_2.0.0.json
   ```
4. Open the PR describing *why*, not just *what*.

## Adding a contract dialect

Contracts live in `examples/contracts/`. A new dialect needs:

- a versioned contract JSON (FieldSpec entries with dotted paths),
- a fixture set in `examples/fixtures/`,
- a diff example that shows a compatible, a forward, and a breaking change.

## Reporting issues

Use the bug template with the smallest contract/envelope pair that
misbehaves - one JSON file each is usually enough.

## Code style

- `pytest -q` stays green; report output is golden-tested.
- Rule names (`field.type.narrowed`, `revision.hint`, ...) are part of the
  API and never renamed without a major version.
