import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = [sys.executable, "-m", "protocolarc"]


def _run(*args):
    return subprocess.run(CLI + list(args), cwd=str(ROOT), capture_output=True, text=True)


def test_contracts_load():
    from protocolarc.loader import load_contract
    c100 = load_contract(ROOT / "examples" / "contracts" / "mcp_tool_call_1.0.0.json")
    c200 = load_contract(ROOT / "examples" / "contracts" / "mcp_tool_call_2.0.0.json")
    assert c100.revision == "1.0.0"
    assert c200.revision == "2.0.0"


