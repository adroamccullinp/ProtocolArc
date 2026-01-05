"""Core data model for ProtocolArc.

A *contract* describes the shape of a protocol envelope: which fields are
required, their JSON types, permitted enumeration values, and nested field
groups. A contract carries a semantic *revision* so revisions of the same
protocol can be compared over time.

An *envelope* is a concrete instance — one MCP/A2A-style message that either
satisfies a contract or violates it.

Everything here is standard-library only and deliberately deterministic:
field ordering is preserved, and derived collections are always sorted so
that repeated runs produce byte-identical output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# JSON type names understood by ProtocolArc. These map onto the seven JSON
# value kinds plus a permissive "any".
JSON_TYPES = ("string", "integer", "number", "boolean", "object", "array", "null", "any")


class ContractError(Exception):
    """Raised when a contract or envelope document is structurally invalid.

    This is distinct from a *validation* finding: a ContractError means the
    document could not be understood at all, whereas a validation finding means
    the document was understood but did not satisfy a contract.
    """


@dataclass(frozen=True)
class FieldSpec:
    """Specification for a single field inside a contract.

    Attributes:
        name:      Dotted path of the field, e.g. ``payload.tool_name``.
        types:     Tuple of accepted JSON type names (see ``JSON_TYPES``).
        required:  Whether the field must be present.
        enum:      Optional tuple of permitted scalar values.
        doc:       Human-readable description used in reports.
    """

    name: str
    types: Tuple[str, ...]
    required: bool = True
    enum: Optional[Tuple[Any, ...]] = None
    doc: str = ""

    def accepts_type(self, type_name: str) -> bool:
        return "any" in self.types or type_name in self.types

    def type_label(self) -> str:
        return "|".join(self.types)


@dataclass
class Contract:
    """A versioned protocol contract.

    Attributes:
        name:      Stable protocol identifier, e.g. ``mcp.tool_call``.
        revision:  Semantic revision string, e.g. ``1.2.0``.
        kind:      Protocol family label, e.g. ``mcp`` or ``a2a``.
        title:     Human title for reports.
        fields:    Ordered list of FieldSpec entries.
        strict:    When True, fields not listed in the contract are findings.
    """

    name: str
    revision: str
    kind: str = "generic"
    title: str = ""
    fields: List[FieldSpec] = field(default_factory=list)
    strict: bool = False

    def field_map(self) -> Dict[str, FieldSpec]:
        return {f.name: f for f in self.fields}

    def field_names(self) -> Tuple[str, ...]:
        return tuple(f.name for f in self.fields)

    def required_names(self) -> Tuple[str, ...]:
        return tuple(f.name for f in self.fields if f.required)

    def revision_tuple(self) -> Tuple[int, ...]:
        """Parse the revision into a comparable integer tuple.

        Non-numeric or missing components collapse to zero so that malformed
        revisions still sort deterministically rather than raising.
        """

        parts: List[int] = []
        for chunk in str(self.revision).split("."):
            digits = "".join(ch for ch in chunk if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])

    def identity(self) -> str:
        return f"{self.name}@{self.revision}"


@dataclass
class Envelope:
    """A concrete protocol message instance.

    Attributes:
        contract:  The contract name this envelope claims to satisfy.
        revision:  The contract revision this envelope targets (optional).
        data:      The raw decoded JSON body of the envelope.
        source:    Provenance label (file name or ``<inline>``).
    """

    contract: str
    revision: Optional[str]
    data: Dict[str, Any]
    source: str = "<inline>"

    def identity(self) -> str:
        rev = self.revision or "?"
        return f"{self.contract}@{rev}:{self.source}"


def json_type_of(value: Any) -> str:
    """Return the ProtocolArc type name for a decoded JSON value."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "any"


def resolve_path(data: Dict[str, Any], dotted: str) -> Tuple[bool, Any]:
    """Resolve a dotted path within a decoded object.

    Returns a ``(present, value)`` tuple. ``present`` is False when any segment
    of the path is missing, allowing the validator to distinguish an absent
    field from a field explicitly set to ``null``.
    """

    cursor: Any = data
    for segment in dotted.split("."):
        if not isinstance(cursor, dict) or segment not in cursor:
            return (False, None)
        cursor = cursor[segment]
    return (True, cursor)
