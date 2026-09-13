"""IP-SAKTI Sahayak Backend root package."""

import sys
from pathlib import Path

_current_dir = Path(__file__).resolve().parent
_repo_root = _current_dir.parent
for _p in (str(_repo_root), str(_current_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
