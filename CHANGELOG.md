# Changelog

All notable changes to this project are documented here.

## [Unreleased]

## [0.5.0] - 2026-08-05

### Added
- `.NET 9` runtime (`runtime/`): loads contracts and validates envelopes
  outside Python; same finding semantics as the CLI.
- A2A `task.send` contract example and fixture set.
- `matrix` cross-checks every envelope against every contract revision.

### Changed
- Findings are ordered deterministically (path, then rule) across all
  subcommands.

## [0.4.0] - 2024-07-30

### Added
- Compatibility verdicts: `compatible`, `forward`, `breaking` with the
  worst-across-fields rule for `diff`.
- Enum widening/narrowing detection, optional->required tightening.

### Changed
- Structural errors vs validation findings are now strictly separated: a
  malformed envelope raises; a well-formed non-conforming envelope produces
  findings, never an exception.

## [0.3.0] - 2022-11-02

### Added
- `FieldSpec` model: dotted paths, accepted types, required flag, enum,
  strict mode flagging undeclared top-level keys.
- Contract loading from JSON with schema-shape checks.
