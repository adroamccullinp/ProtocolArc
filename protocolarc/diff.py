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
