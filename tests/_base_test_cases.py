"""
tests/_base_test_cases.py

For the creation of more modular tests, I have decided to create custom TestCase classes which can
be implemented by other test files.
"""

import tornado.platform.asyncio
import tornado.testing
import unittest.mock

from unittest.mock import MagicMock

from src.server import ServerApp
from tests.fixtures import create_fixture_func, create_config_parser_fixture


class MyServerTestCase(tornado.testing.AsyncHTTPTestCase):
    """Tornado server"""

    def stub_validate_auth_token(self, *return_values):
        """Convenience method for stubbing application.stub_validate_auth_token."""

        # Create a mocked function with the passed return values
        stub = MagicMock(side_effect=return_values)

        # Create a co-routine proxy for the stub
        async def proxy(*args, **kwargs):
            return stub(*args, **kwargs)

        # Assign the stub to the server app instance
        self._app.validate_auth_token = proxy

        # Return the stub so checks can be made (like stub.assert_called_once)
        return stub

    def stub_db_execute(self, *return_values):
        """Convenience method for stubbing application.stub_validate_auth_token."""

        # Create a mocked function with the passed return values
        stub = MagicMock(side_effect=return_values)

        # Create a co-routine proxy for the stub
        async def proxy(*args, **kwargs):
            return stub(*args, **kwargs)

        # Assign the stub to the server app instance
        self._app.db.execute = proxy

        # Return the stub so checks can be made (like stub.assert_called_once)
        return stub

    def get_new_ioloop(self):
        """Overwrite the base IOLoop with the asyncio loop."""
        return tornado.platform.asyncio.AsyncIOLoop.instance()

    @unittest.mock.patch('src.server.DB', create_fixture_func)
    @unittest.mock.patch('src.server.JobScheduler', create_fixture_func)
    @unittest.mock.patch('src.server.ConfigParser', create_config_parser_fixture)
    def get_app(self):
        """Return a mocked version of the veggiecron server."""
        app = ServerApp(self.io_loop)
        return app
