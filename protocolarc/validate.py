"""Envelope validation against a contract.

Validation produces a ``ValidationResult`` holding an ordered, deterministic
list of ``Finding`` objects. Each finding names a rule, a field, a severity and
a message. The result never raises for a *content* problem — it only raises for
a *structural* problem via ContractError upstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .model import Contract, Envelope, json_type_of, resolve_path


# Severity ranks; higher is worse. Used for deterministic ordering and exit
# code derivation.
SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}


@dataclass(frozen=True)
class Finding:
    """A single validation observation."""

    rule: str
    field: str
