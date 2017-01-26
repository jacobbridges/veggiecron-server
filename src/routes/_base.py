"""
src/routes/_base.py

Base route for which all other routes should inherit from.
"""

from tornado.web import RequestHandler

from ..scheduler import JobScheduler


class BasePageHandler(RequestHandler):
    """Base handler with common functions to make available to all other handlers."""

    def data_received(self, chunk):
        """Implement this method to handle streamed request data."""

    @property
    def db(self):
        return self.application.db

    @property
    def scheduler(self) -> JobScheduler:
        return self.application.scheduler

    async def get_cursor(self):
        return await self.application.db.cursor()

    async def validate_auth_token(self, token_base64):
        return await self.application.validate_auth_token(token_base64)

    async def generate_auth_token(self, user_id):
        return await self.application.generate_auth_token(user_id)
