"""ProtocolArc — an agent protocol contract lab.

ProtocolArc models MCP/A2A-style message envelopes as versioned contracts,
validates instances against those contracts, compares contract revisions to
classify compatibility changes, and renders a deterministic contract matrix
and report.

Public surface:
    load_contract          Parse a contract document into a Contract.
    load_envelope          Parse an envelope instance into an Envelope.
    validate_envelope      Validate an envelope against a contract.
    diff_contracts         Compare two contract revisions.
    build_matrix           Build a contract compatibility matrix.
    render_report          Render a deterministic report document.
"""

from .model import (
    Contract,
    Envelope,
    FieldSpec,
    ContractError,
)
from .loader import load_contract, load_envelope, load_contract_dir
from .validate import validate_envelope, ValidationResult, Finding
from .diff import diff_contracts, ContractDiff, Change, Compatibility
from .matrix import build_matrix, ContractMatrix
from .report import render_report

__all__ = [
    "Contract",
    "Envelope",
    "FieldSpec",
    "ContractError",
    "load_contract",
    "load_envelope",
    "load_contract_dir",
    "validate_envelope",
    "ValidationResult",
    "Finding",
    "diff_contracts",
    "ContractDiff",
    "Change",
    "Compatibility",
    "build_matrix",
    "ContractMatrix",
    "render_report",
]

__version__ = "0.4.0"
