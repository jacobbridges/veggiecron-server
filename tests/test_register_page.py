"""
tests/test_register_page.py

Test the register page ("/register"). A get request will show information on how to register with
the server, and a post request should register a user with the server.
"""

import json
import pytest
import tornado.gen
import tornado.testing
import tornado.httpclient

from src.routes.register import RegisterPageHandler
from tests._base_test_cases import MyServerTestCase


class TestGetRegisterPage(MyServerTestCase):
    """GET register route '/register'"""

    def test_response_code(self):
        """Should have an HTTP response code of 200."""
        response = self.fetch('/register')
        self.assertEqual(response.code, 200)

    def test_response_is_json(self):
        """Should have JSON encoded body."""
        response = self.fetch('/register')
        try:
            json.loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    def test_response_has_help_text(self):
        """Should have the register help text in the response body."""
        response = self.fetch('/register')
        self.assertEqual(type(response.body), bytes)
        self.assertIn(json.dumps(RegisterPageHandler.get_description),
                      response.body.decode('utf-8'))

    def test_response_has_post_arguments_help(self):
        """Should have information about the post arguments in the response body."""
        response = self.fetch('/register')
        self.assertEqual(type(response.body), bytes)
        json_response = json.loads(response.body.decode('utf8'))
        self.assertIn('data', json_response)
        self.assertDictEqual(json_response['data'], RegisterPageHandler.post_args)


class TestPostRegisterPage(MyServerTestCase):
    """POST register route '/register'"""

    @tornado.testing.gen_test
    def test_response_code(self):
        """Should have an HTTP response code of 400 when no arguments are supplied."""
        future = self.http_client.fetch(self.get_url('/register'), method='POST', body='')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)
