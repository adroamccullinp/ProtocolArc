"""Contract compatibility matrix.

A matrix cross-references a set of envelopes against a set of contracts and
records, for each pair, whether the envelope validates. It also groups
contracts by name and builds a revision chain so the report can show how a
protocol evolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .model import Contract, Envelope
from .validate import validate_envelope, ValidationResult
from .diff import diff_contracts, ContractDiff


@dataclass
class Cell:
    """One envelope-vs-contract validation outcome."""

    envelope: str
    contract: str
    revision: str
    ok: bool
    errors: int
    warnings: int


@dataclass
class ContractMatrix:
    """The full cross product of envelopes and contracts plus revision chains."""

    cells: List[Cell] = field(default_factory=list)
    diffs: List[ContractDiff] = field(default_factory=list)
    contract_ids: List[str] = field(default_factory=list)
    envelope_ids: List[str] = field(default_factory=list)

    def cell_for(self, envelope: str, contract_id: str):
        for c in self.cells:
            if c.envelope == envelope and f"{c.contract}@{c.revision}" == contract_id:
                return c
        return None

    def pass_rate(self) -> float:
        if not self.cells:
            return 1.0
        passed = sum(1 for c in self.cells if c.ok)
        return round(passed / len(self.cells), 4)


def _revision_chains(contracts: List[Contract]) -> List[ContractDiff]:
    """Build diffs between consecutive revisions of each contract name."""

    by_name: Dict[str, List[Contract]] = {}
    for contract in contracts:
        by_name.setdefault(contract.name, []).append(contract)

    diffs: List[ContractDiff] = []
    for name in sorted(by_name):
        chain = sorted(by_name[name], key=lambda c: c.revision_tuple())
        for older, newer in zip(chain, chain[1:]):
            diffs.append(diff_contracts(older, newer))
    return diffs


def build_matrix(contracts: List[Contract], envelopes: List[Envelope]) -> ContractMatrix:
