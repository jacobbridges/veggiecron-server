"""
src/routes/index.py

Index "/" route for all HTTP methods.
"""

import json

from ._base import BasePageHandler


class IndexPageHandler(BasePageHandler):
    """Page handler for index ('/') route."""

    def get(self):
        self.write(json.dumps(self.application.settings))
