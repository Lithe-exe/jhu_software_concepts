"""Bridge fixtures so `pytest src/` can use the main test fixtures."""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from tests.conftest import *  # noqa: F401,F403
