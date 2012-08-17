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
        sys.stdout.write(f"compatibility: {diff.compatibility.value.upper()}\n")
        for c in diff.sorted_changes():
            sys.stdout.write(f"  {c.impact.value:11} {c.kind:26} {c.field}: {c.detail}\n")
        if not diff.changes:
            sys.stdout.write("  (no changes)\n")

    return 2 if diff.compatibility == Compatibility.BREAKING else 0


def _load_contracts(paths: List[str]):
    contracts = []
    for path in paths:
        import os

        if os.path.isdir(path):
            contracts.extend(load_contract_dir(path))
        else:
            contracts.append(load_contract(path))
    return contracts


def _cmd_matrix(args) -> int:
    contracts = _load_contracts(args.contracts)
    envelopes = []
    for env_path in args.envelopes:
        envelopes.extend(load_envelope(env_path))
    matrix = build_matrix(contracts, envelopes)
    sys.stdout.write(render_report(matrix, fmt=args.format))
    all_ok = all(c.ok for c in matrix.cells)
    return 0 if all_ok else 1


def _cmd_report(args) -> int:
    contracts = _load_contracts(args.contracts)
    envelopes = []
    for env_path in args.envelopes:
        envelopes.extend(load_envelope(env_path))
    matrix = build_matrix(contracts, envelopes)
    output = render_report(matrix, fmt=args.format)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(output)
        sys.stdout.write(f"wrote {args.out}\n")
    else:
        sys.stdout.write(output)
    return 0


def _cmd_describe(args) -> int:
    contract = load_contract(args.contract)
    sys.stdout.write(f"{contract.title} [{contract.kind}] {contract.identity()}\n")
    sys.stdout.write(f"strict={contract.strict} fields={len(contract.fields)}\n")
    for spec in contract.fields:
        req = "required" if spec.required else "optional"
        enum = f" enum={list(spec.enum)}" if spec.enum else ""
        sys.stdout.write(f"  {spec.name:28} {spec.type_label():18} {req}{enum}\n")
        if spec.doc:
            sys.stdout.write(f"      {spec.doc}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="protocolarc",
        description="ProtocolArc — an agent protocol contract lab.",
