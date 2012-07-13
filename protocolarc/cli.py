"""Command-line interface for ProtocolArc.

Commands
--------
    validate   Validate envelopes against a contract.
    diff       Compare two contract revisions and classify compatibility.
    matrix     Cross-validate envelopes against a directory of contracts.
    report     Render a full contract matrix/report.
    describe   Print a contract's field table.

The CLI reads structured JSON/JSONL input and emits deterministic output.
Exit codes:
    0  success, no validation errors
    1  validation errors present
    2  breaking compatibility detected (diff command)
    3  usage or input error
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from . import __version__
from .loader import (
    load_contract,
    load_contract_dir,
    load_envelope,
)
from .model import ContractError
