from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_PYTHON = ROOT / "sdk/python"

for candidate in (ROOT, SDK_PYTHON):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
