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
