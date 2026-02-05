"""Deterministic report rendering.

Reports come in three shapes:

* ``json``      — a structured, sorted JSON document suitable for machine use.
* ``markdown``  — a human-readable contract matrix and revision log.
* ``text``      — a compact terminal summary.

All renderers are pure functions of their inputs and emit stable ordering, so
the same inputs always produce byte-identical output.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .matrix import ContractMatrix
from .validate import ValidationResult


def _matrix_to_dict(matrix: ContractMatrix) -> Dict[str, Any]:
    return {
        "summary": {
            "contracts": len(matrix.contract_ids),
            "envelopes": len(set(matrix.envelope_ids)),
            "cells": len(matrix.cells),
            "pass_rate": matrix.pass_rate(),
            "revision_diffs": len(matrix.diffs),
        },
        "contracts": matrix.contract_ids,
        "envelopes": sorted(set(matrix.envelope_ids)),
        "cells": [
            {
                "envelope": c.envelope,
                "contract": c.contract,
                "revision": c.revision,
                "ok": c.ok,
                "errors": c.errors,
                "warnings": c.warnings,
            }
            for c in sorted(
                matrix.cells, key=lambda x: (x.contract, x.revision, x.envelope)
            )
        ],
        "diffs": [
            {
                "name": d.name,
                "from": d.old_revision,
                "to": d.new_revision,
                "compatibility": d.compatibility.value,
                "changes": [
                    {"kind": ch.kind, "field": ch.field, "impact": ch.impact.value, "detail": ch.detail}
                    for ch in d.sorted_changes()
                ],
            }
            for d in sorted(matrix.diffs, key=lambda d: (d.name, d.new_revision))
        ],
    }


def _render_json(matrix: ContractMatrix) -> str:
    return json.dumps(_matrix_to_dict(matrix), indent=2, sort_keys=True)


def _badge(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _render_markdown(matrix: ContractMatrix) -> str:
    lines: List[str] = []
    lines.append("# ProtocolArc Contract Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Contracts: {len(matrix.contract_ids)}")
    lines.append(f"- Envelopes: {len(set(matrix.envelope_ids))}")
    lines.append(f"- Validation cells: {len(matrix.cells)}")
    lines.append(f"- Pass rate: {matrix.pass_rate() * 100:.1f}%")
    lines.append("")

    lines.append("## Contract Matrix")
    lines.append("")
    envelopes = sorted(set(matrix.envelope_ids))
    header = "| Contract | " + " | ".join(envelopes) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(envelopes)) + " |"
    lines.append(header)
    lines.append(sep)
    for contract_id in matrix.contract_ids:
        row = [contract_id]
        for env in envelopes:
            cell = matrix.cell_for(env, contract_id)
            if cell is None:
                row.append("-")
            else:
                mark = _badge(cell.ok)
                if cell.warnings:
                    mark += f" ({cell.warnings}w)"
                row.append(mark)
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    if matrix.diffs:
        lines.append("## Revision Log")
        lines.append("")
        for d in sorted(matrix.diffs, key=lambda d: (d.name, d.new_revision)):
            lines.append(f"### {d.name}: {d.old_revision} -> {d.new_revision}")
            lines.append("")
            lines.append(f"Compatibility: **{d.compatibility.value.upper()}**")
            lines.append("")
            if not d.changes:
                lines.append("_No field-level changes._")
                lines.append("")
                continue
            lines.append("| Field | Change | Impact | Detail |")
            lines.append("| --- | --- | --- | --- |")
            for ch in d.sorted_changes():
                lines.append(f"| {ch.field} | {ch.kind} | {ch.impact.value} | {ch.detail} |")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_text(matrix: ContractMatrix) -> str:
    lines: List[str] = []
    lines.append("ProtocolArc report")
    lines.append(f"  contracts={len(matrix.contract_ids)} "
                 f"envelopes={len(set(matrix.envelope_ids))} "
                 f"pass_rate={matrix.pass_rate() * 100:.1f}%")
    for c in sorted(matrix.cells, key=lambda x: (x.contract, x.revision, x.envelope)):
        lines.append(
            f"  [{_badge(c.ok)}] {c.contract}@{c.revision} <- {c.envelope} "
            f"(err={c.errors} warn={c.warnings})"
        )
    for d in sorted(matrix.diffs, key=lambda d: (d.name, d.new_revision)):
        lines.append(
            f"  diff {d.name} {d.old_revision}->{d.new_revision}: "
            f"{d.compatibility.value} ({len(d.changes)} changes)"
        )
    return "\n".join(lines) + "\n"


def render_report(matrix: ContractMatrix, fmt: str = "markdown") -> str:
    """Render a matrix into the requested format."""

    if fmt == "json":
        return _render_json(matrix)
    if fmt == "text":
        return _render_text(matrix)
    if fmt == "markdown":
        return _render_markdown(matrix)
    raise ValueError(f"unknown report format '{fmt}'")


def render_validation(results: List[ValidationResult], fmt: str = "text") -> str:
    """Render a list of validation results (used by the ``validate`` command)."""

    if fmt == "json":
        payload = [
            {
                "envelope": r.envelope,
                "contract": r.contract,
                "revision": r.revision,
                "ok": r.ok,
                "findings": [
                    {"rule": f.rule, "field": f.field, "severity": f.severity, "message": f.message}
                    for f in r.sorted_findings()
                ],
            }
            for r in sorted(results, key=lambda r: (r.contract, r.envelope))
        ]
        return json.dumps(payload, indent=2, sort_keys=True)

    lines: List[str] = []
    for r in sorted(results, key=lambda r: (r.contract, r.envelope)):
        status = "PASS" if r.ok else "FAIL"
        lines.append(f"[{status}] {r.contract}@{r.revision} <- {r.envelope}")
        for f in r.sorted_findings():
            lines.append(f"    {f.severity.upper():7} {f.rule:22} {f.field}: {f.message}")
    if not lines:
        lines.append("no results")
    return "\n".join(lines) + "\n"
