"""
src/routes/index.py

Index "/" route for all HTTP methods.
"""

from ._base import BasePageHandler


class IndexPageHandler(BasePageHandler):
    """Page handler for index ('/') route."""

    def get(self):
        self.write(self.application.settings)
