"""
tests/_base_test_cases.py

For the creation of more modular tests, I have decided to create custom TestCase classes which can
be implemented by other test files.
"""

import tornado.platform.asyncio
import tornado.testing
import unittest.mock

from src.server import ServerApp
from tests.fixtures import (create_db_fixture, create_job_scheduler_fixture,
                            create_config_parser_fixture)


class MyServerTestCase(tornado.testing.AsyncHTTPTestCase):
    """Tornado server"""

    def get_new_ioloop(self):
        """Overwrite the base IOLoop with the asyncio loop."""
        return tornado.platform.asyncio.AsyncIOLoop.instance()

    @unittest.mock.patch('src.server.DB', create_db_fixture())
    @unittest.mock.patch('src.server.JobScheduler', create_job_scheduler_fixture())
    @unittest.mock.patch('src.server.ConfigParser', create_config_parser_fixture)
    def get_app(self):
        """Return a mocked version of the veggiecron server."""
        app = ServerApp(self.io_loop)
        return app
