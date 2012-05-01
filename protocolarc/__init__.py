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
