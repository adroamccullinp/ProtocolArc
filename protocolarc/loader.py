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

