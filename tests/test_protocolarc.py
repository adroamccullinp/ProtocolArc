import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = [sys.executable, "-m", "protocolarc"]


def _run(*args):
    return subprocess.run(CLI + list(args), cwd=str(ROOT), capture_output=True, text=True)


