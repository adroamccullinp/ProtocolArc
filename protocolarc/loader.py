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
        raise ContractError(f"{source}: 'fields' must be a list")

    fields: List[FieldSpec] = []
    seen = set()
    for idx, fraw in enumerate(fields_raw):
        where = f"{source}: fields[{idx}]"
        if not isinstance(fraw, dict):
            raise ContractError(f"{where}: each field must be an object")
        fname = _require(fraw, "name", where)
        if fname in seen:
            raise ContractError(f"{where}: duplicate field name '{fname}'")
        seen.add(fname)
        types = _as_type_tuple(_require(fraw, "type", where), where)
        enum_raw = fraw.get("enum")
        enum = tuple(enum_raw) if isinstance(enum_raw, list) else None
        fields.append(
            FieldSpec(
                name=str(fname),
                types=types,
                required=bool(fraw.get("required", True)),
                enum=enum,
                doc=str(fraw.get("doc", "")),
            )
        )

    return Contract(
        name=str(name),
        revision=str(revision),
        kind=str(doc.get("kind", "generic")),
        title=str(doc.get("title", name)),
        fields=fields,
        strict=bool(doc.get("strict", False)),
    )


def parse_envelope(doc: Dict[str, Any], source: str = "<inline>") -> Envelope:
    """Build an Envelope from a decoded envelope document.

    Two shapes are accepted:

    * *Wrapped* — an object with ``contract``, optional ``revision`` and a
      ``data`` body. This is the canonical form.
    * *Bare* — any object that carries a top-level ``contract`` key; the whole
      object (minus the routing keys) becomes the data body.
    """

    if not isinstance(doc, dict):
        raise ContractError(f"{source}: envelope must be a JSON object")

    contract = _require(doc, "contract", source)
    revision = doc.get("revision")

    if "data" in doc and isinstance(doc["data"], dict):
        data = doc["data"]
    else:
        data = {k: v for k, v in doc.items() if k not in ("contract", "revision")}

    return Envelope(
        contract=str(contract),
        revision=str(revision) if revision is not None else None,
        data=data,
        source=source,
    )


def load_contract(path: str) -> Contract:
    """Load a single contract from a JSON file."""

    with open(path, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    return parse_contract(doc, source=os.path.basename(path))


def load_contract_dir(path: str) -> List[Contract]:
    """Load every ``*.json`` contract in a directory, sorted by file name."""

    contracts: List[Contract] = []
    for entry in sorted(os.listdir(path)):
        if entry.endswith(".json"):
            contracts.append(load_contract(os.path.join(path, entry)))
    return contracts


def load_envelope(path: str) -> List[Envelope]:
    """Load envelopes from a ``.json`` (single/array) or ``.jsonl`` file."""

    base = os.path.basename(path)
    envelopes: List[Envelope] = []
    if path.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                envelopes.append(parse_envelope(doc, source=f"{base}:{lineno}"))
        return envelopes

    with open(path, "r", encoding="utf-8") as handle:
        doc = json.load(handle)
    if isinstance(doc, list):
        for idx, item in enumerate(doc):
            envelopes.append(parse_envelope(item, source=f"{base}[{idx}]"))
    else:
        envelopes.append(parse_envelope(doc, source=base))
    return envelopes
