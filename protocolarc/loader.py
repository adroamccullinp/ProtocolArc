"""Loaders that turn JSON/JSONL documents into model objects.

Contract documents and envelope documents are both plain JSON. The loader is
tolerant of ordering but strict about shape: a malformed document raises
``ContractError`` with a precise message rather than silently degrading.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from .model import Contract, Envelope, FieldSpec, ContractError, JSON_TYPES


def _require(doc: Dict[str, Any], key: str, where: str) -> Any:
    if key not in doc:
        raise ContractError(f"{where}: missing required key '{key}'")
    return doc[key]


def _as_type_tuple(raw: Any, where: str):
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list) or not raw:
        raise ContractError(f"{where}: 'type' must be a string or non-empty list")
    types = tuple(str(t) for t in raw)
    for t in types:
        if t not in JSON_TYPES:
            raise ContractError(
                f"{where}: unknown type '{t}'; expected one of {', '.join(JSON_TYPES)}"
            )
    return types


def parse_contract(doc: Dict[str, Any], source: str = "<inline>") -> Contract:
    """Build a Contract from a decoded contract document."""

    if not isinstance(doc, dict):
        raise ContractError(f"{source}: contract must be a JSON object")

    name = _require(doc, "name", source)
    revision = _require(doc, "revision", source)
    fields_raw = doc.get("fields", [])
    if not isinstance(fields_raw, list):
