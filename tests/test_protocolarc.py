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


def test_validate_cli_passes_and_flags():
    r = _run("validate", "examples/contracts/mcp_tool_call_1.1.0.json",
             "examples/fixtures/mcp_calls.jsonl")
    assert r.returncode in (0, 1)
    assert "[PASS]" in r.stdout


def test_older_contract_flags_enum():
    r = _run("validate", "examples/contracts/mcp_tool_call_1.0.0.json",
             "examples/fixtures/mcp_calls.jsonl")
    assert "field.enum" in r.stdout


def test_diff_is_breaking():
    r = _run("diff", "examples/contracts/mcp_tool_call_1.0.0.json",
             "examples/contracts/mcp_tool_call_2.0.0.json")
    assert "BREAKING" in r.stdout


def test_a2a_fixture_shape():
    a2a = json.loads((ROOT / "examples" / "fixtures" / "a2a_tasks.json").read_text(encoding="utf-8"))
    assert isinstance(a2a, list) and a2a
