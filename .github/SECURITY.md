# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.5.x   | yes       |
| < 0.5   | no        |

## Reporting a vulnerability

ProtocolArc parses offline JSON documents, so the surface is narrow:

- unbounded memory on deeply nested or huge contract/envelope files,
- quadratic behaviour on adversarial FieldSpec paths,
- report injection: contract and envelope strings must be escaped in the
  markdown renderer so a crafted name cannot smuggle markup.

Please do **not** open a public issue for these. Contact the repository
owner through the profile with:

1. The affected version (`protocolarc --version` or the commit SHA).
2. The smallest JSON input that triggers the behaviour.
3. Expected vs. actual behaviour.

You will get an acknowledgement within a week. Fixes land in the next minor
release and the reporter is credited in the changelog unless they prefer
otherwise.

## Scope

- `loader.py` - untrusted input, primary focus.
- `validate.py` / `diff.py` - matching and comparison logic.
- `report.py` - escaping of document-derived strings in output.
- `runtime/` - must stay semantically identical to the CLI.
