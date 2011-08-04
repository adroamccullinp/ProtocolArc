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
