"""Command-line interface for ProtocolArc.

Commands
--------
    validate   Validate envelopes against a contract.
    diff       Compare two contract revisions and classify compatibility.
    matrix     Cross-validate envelopes against a directory of contracts.
    report     Render a full contract matrix/report.
    describe   Print a contract's field table.

The CLI reads structured JSON/JSONL input and emits deterministic output.
Exit codes:
    0  success, no validation errors
    1  validation errors present
    2  breaking compatibility detected (diff command)
    3  usage or input error
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from . import __version__
from .loader import (
    load_contract,
    load_contract_dir,
    load_envelope,
)
from .model import ContractError
from .validate import validate_envelope
from .diff import diff_contracts, Compatibility
from .matrix import build_matrix
from .report import render_report, render_validation


def _cmd_validate(args) -> int:
    contract = load_contract(args.contract)
    results = []
    for env_path in args.envelopes:
        for envelope in load_envelope(env_path):
            results.append(validate_envelope(contract, envelope))
    sys.stdout.write(render_validation(results, fmt=args.format))
    return 0 if all(r.ok for r in results) else 1


def _cmd_diff(args) -> int:
    old = load_contract(args.old)
    new = load_contract(args.new)
    diff = diff_contracts(old, new)

    if args.format == "json":
        import json

        payload = {
            "name": diff.name,
            "from": diff.old_revision,
            "to": diff.new_revision,
            "compatibility": diff.compatibility.value,
            "changes": [
                {"kind": c.kind, "field": c.field, "impact": c.impact.value, "detail": c.detail}
                for c in diff.sorted_changes()
            ],
        }
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(
            f"{diff.name}: {diff.old_revision} -> {diff.new_revision}\n"
        )
