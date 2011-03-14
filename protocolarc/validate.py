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
    return value in spec.enum


def validate_envelope(contract: Contract, envelope: Envelope) -> ValidationResult:
    """Validate an envelope against a contract, returning ordered findings."""

    result = ValidationResult(
        envelope=envelope.source,
        contract=contract.name,
        revision=contract.revision,
    )

    # Rule: contract-name match. A mismatch is an error because the envelope is
    # being checked against the wrong contract.
    if envelope.contract != contract.name:
        result.findings.append(
            Finding(
                rule="contract.match",
                field="<envelope>",
                severity="error",
                message=(
                    f"envelope targets '{envelope.contract}' "
                    f"but validated against '{contract.name}'"
                ),
            )
        )

    # Rule: revision hint. A mismatch is a warning — the envelope may be an
    # older client talking to a newer contract.
    if envelope.revision and envelope.revision != contract.revision:
        result.findings.append(
            Finding(
                rule="revision.hint",
                field="<envelope>",
                severity="warning",
                message=(
                    f"envelope declares revision '{envelope.revision}', "
                    f"contract is '{contract.revision}'"
                ),
            )
        )

    field_map = contract.field_map()

    # Per-field rules.
    for spec in contract.fields:
        present, value = resolve_path(envelope.data, spec.name)

        if not present:
            if spec.required:
                result.findings.append(
                    Finding(
                        rule="field.required",
                        field=spec.name,
                        severity="error",
                        message=f"required field '{spec.name}' is missing",
                    )
                )
            continue

        actual = json_type_of(value)
        if not spec.accepts_type(actual):
            result.findings.append(
                Finding(
                    rule="field.type",
                    field=spec.name,
                    severity="error",
                    message=(
                        f"field '{spec.name}' has type '{actual}', "
                        f"expected '{spec.type_label()}'"
                    ),
                )
            )
            continue

        if not _check_enum(spec, value):
            allowed = ", ".join(repr(e) for e in spec.enum)
