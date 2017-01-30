"""
tests/test_index_page.py

Test the base route ("/") of the server, the index page. The index page should show information
about the server.
"""

import pytest

from tests._base_test_cases import MyServerTestCase
from tests.fixtures import create_config_parser_fixture


class TestGetIndexPage(MyServerTestCase):
    """GET '/'"""

    def test_response_code(self):
        """Should have an HTTP response code of 200."""
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

    def test_response_is_json(self):
        """Should have JSON encoded body."""
        response = self.fetch('/')
        from json import loads
        try:
            loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    def test_response_has_app_name(self):
        """Should have the application name in the body."""
        response = self.fetch('/')
        config = create_config_parser_fixture()
        self.assertIn(config.app_name, str(response.body))
