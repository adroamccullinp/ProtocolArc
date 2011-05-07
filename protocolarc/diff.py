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
        return sorted(self.changes, key=lambda c: c.sort_key())


def _type_relation(old: FieldSpec, new: FieldSpec) -> List[Change]:
    old_types = set(old.types)
    new_types = set(new.types)
    if old_types == new_types:
        return []
    changes: List[Change] = []
    if "any" in new_types and "any" not in old_types:
        return [Change("field.type.widened", new.name, f"{old.type_label()} -> any")]
    if "any" in old_types and "any" not in new_types:
        return [Change("field.type.narrowed", new.name, f"any -> {new.type_label()}")]
    if old_types <= new_types:
        changes.append(
            Change("field.type.widened", new.name, f"{old.type_label()} -> {new.type_label()}")
        )
    elif new_types <= old_types:
        changes.append(
            Change("field.type.narrowed", new.name, f"{old.type_label()} -> {new.type_label()}")
        )
    else:
        # Overlapping but neither subset: removed members are narrowing.
        changes.append(
            Change("field.type.narrowed", new.name, f"{old.type_label()} -> {new.type_label()}")
        )
    return changes


def _enum_relation(old: FieldSpec, new: FieldSpec) -> List[Change]:
    if old.enum is None and new.enum is None:
        return []
    if old.enum is None and new.enum is not None:
        return [Change("field.enum.added", new.name, f"added enum {list(new.enum)!r}")]
    if old.enum is not None and new.enum is None:
        return [Change("field.enum.removed", new.name, "enum constraint removed")]
    old_set = set(old.enum or ())
    new_set = set(new.enum or ())
    if old_set == new_set:
        return []
    changes: List[Change] = []
    if new_set < old_set:
        changes.append(Change("field.enum.restricted", new.name, f"removed {sorted(old_set - new_set)!r}"))
    elif old_set < new_set:
        changes.append(Change("field.enum.expanded", new.name, f"added {sorted(new_set - old_set)!r}"))
    else:
        changes.append(Change("field.enum.restricted", new.name, "enum membership changed"))
    return changes


def diff_contracts(old: Contract, new: Contract) -> ContractDiff:
    """Compute the field-level diff between two contract revisions."""

    diff = ContractDiff(
        name=new.name,
        old_revision=old.revision,
        new_revision=new.revision,
    )

    old_map: Dict[str, FieldSpec] = old.field_map()
    new_map: Dict[str, FieldSpec] = new.field_map()

    # Added fields.
    for name in new_map:
        if name not in old_map:
            spec = new_map[name]
            kind = "field.added.required" if spec.required else "field.added.optional"
            diff.changes.append(Change(kind, name, f"added {spec.type_label()}"))

