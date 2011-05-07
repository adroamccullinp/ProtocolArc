"""Contract revision comparison and compatibility classification.

Given two revisions of the same contract, ``diff_contracts`` enumerates the
field-level changes and classifies the overall compatibility outcome using a
small, explicit rule set.

Compatibility model
--------------------
* ``COMPATIBLE``    — new revision accepts everything the old one did.
* ``FORWARD``       — old consumers keep working; new fields are optional.
* ``BREAKING``      — a change can reject previously-valid envelopes.

The classification is the *worst* outcome across all detected changes, so a
single breaking change makes the whole diff breaking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from .model import Contract, FieldSpec


class Compatibility(Enum):
    COMPATIBLE = "compatible"
    FORWARD = "forward"
    BREAKING = "breaking"

    @property
    def rank(self) -> int:
        return {"compatible": 0, "forward": 1, "breaking": 2}[self.value]


# Each change kind maps to the compatibility impact it implies.
CHANGE_IMPACT = {
    "field.added.required": Compatibility.BREAKING,
    "field.added.optional": Compatibility.FORWARD,
    "field.removed.required": Compatibility.BREAKING,
    "field.removed.optional": Compatibility.FORWARD,
    "field.type.narrowed": Compatibility.BREAKING,
    "field.type.widened": Compatibility.FORWARD,
    "field.required.tightened": Compatibility.BREAKING,
    "field.required.relaxed": Compatibility.FORWARD,
    "field.enum.restricted": Compatibility.BREAKING,
    "field.enum.expanded": Compatibility.FORWARD,
    "field.enum.added": Compatibility.BREAKING,
    "field.enum.removed": Compatibility.FORWARD,
}


@dataclass(frozen=True)
class Change:
    """A single field-level difference between two contract revisions."""

    kind: str
    field: str
    detail: str

    @property
    def impact(self) -> Compatibility:
        return CHANGE_IMPACT.get(self.kind, Compatibility.COMPATIBLE)

    def sort_key(self) -> Tuple[int, str, str]:
        return (-self.impact.rank, self.field, self.kind)


@dataclass
class ContractDiff:
    """Full diff between an ``old`` and ``new`` revision of one contract."""

    name: str
    old_revision: str
    new_revision: str
    changes: List[Change] = field(default_factory=list)

    @property
    def compatibility(self) -> Compatibility:
        worst = Compatibility.COMPATIBLE
        for change in self.changes:
            if change.impact.rank > worst.rank:
                worst = change.impact
        return worst

    def sorted_changes(self) -> List[Change]:
