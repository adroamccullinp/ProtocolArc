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
