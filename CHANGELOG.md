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
