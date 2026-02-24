"""Bridge fixtures so `pytest src/` can use the main test fixtures."""
# pylint: disable=wrong-import-position,wildcard-import,unused-wildcard-import,import-error

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# This bridge re-exports the root test fixtures when pytest is scoped to `src/`.
from tests.conftest import *  # noqa: F401,F403
