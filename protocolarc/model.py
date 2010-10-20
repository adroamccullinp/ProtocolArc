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
