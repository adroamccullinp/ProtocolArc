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


