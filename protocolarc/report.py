"""Deterministic report rendering.

Reports come in three shapes:

* ``json``      — a structured, sorted JSON document suitable for machine use.
* ``markdown``  — a human-readable contract matrix and revision log.
* ``text``      — a compact terminal summary.

All renderers are pure functions of their inputs and emit stable ordering, so
the same inputs always produce byte-identical output.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .matrix import ContractMatrix
