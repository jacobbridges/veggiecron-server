"""
tests/server.py

Test the server object. I will not be testing all methods of the server since the server a child
of tornado.web.Application and the tornado project is tested, I am only testing the custom logic
that was added in this project.
"""

import tornado.platform.asyncio
import tornado.testing
import unittest.mock

from src.server import ServerApp
from tests.fixtures import (create_db_fixture, create_job_scheduler_fixture,
                            create_config_parser_fixture)


class TestServer(tornado.testing.AsyncHTTPTestCase):
    """Start a test instance of the server."""

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

    def test_index(self):
        """Test the index route of the server."""
        response = self.fetch('/')
        config = create_config_parser_fixture()
        self.assertEqual(response.code, 200)
        self.assertIn(config.app_name, str(response.body))
