"""Compatibility module that aliases `web.app` as `app`."""

import sys

from web import app as _web_app

sys.modules[__name__] = _web_app
