"""
Pytest configuration file.

This file modifies ``sys.path`` so that the ``src`` package can be imported
from the tests without installing the project as a package.  It also
ensures that the project root is available on the import path.
"""

import sys
from pathlib import Path

# Add the project root and the src directory to sys.path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))