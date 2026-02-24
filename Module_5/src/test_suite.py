"""
Bridge test module so `pytest src/` collects the project's test suite.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from tests.test_analysis_format import *  # noqa: F401,F403
from tests.test_buttons import *  # noqa: F401,F403
from tests.test_coverage_complete import *  # noqa: F401,F403
from tests.test_coverage_edges import *  # noqa: F401,F403
from tests.test_db_insert import *  # noqa: F401,F403
from tests.test_flask_page import *  # noqa: F401,F403
from tests.test_integration_end_to_end import *  # noqa: F401,F403
from tests.test_load_data_coverage import *  # noqa: F401,F403
from tests.test_unit_internals import *  # noqa: F401,F403
