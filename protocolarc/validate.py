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
    severity: str
    message: str

    def sort_key(self) -> Tuple[int, str, str]:
        return (-SEVERITY_RANK.get(self.severity, 0), self.field, self.rule)


@dataclass
class ValidationResult:
    """Outcome of validating one envelope against one contract."""

    envelope: str
    contract: str
    revision: str
    findings: List[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def counts(self) -> Dict[str, int]:
        out = {"info": 0, "warning": 0, "error": 0}
        for f in self.findings:
            out[f.severity] = out.get(f.severity, 0) + 1
        return out

    def sorted_findings(self) -> List[Finding]:
        return sorted(self.findings, key=lambda f: f.sort_key())


def _check_enum(spec, value) -> bool:
    if spec.enum is None:
        return True
