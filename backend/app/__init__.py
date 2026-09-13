"""IP-SAKTI Sahayak Backend Application Package."""

import sys
from pathlib import Path

_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent
_repo_root = _backend_dir.parent
for _p in (str(_repo_root), str(_backend_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
