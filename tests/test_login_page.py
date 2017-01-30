"""
tests/test_login_page.py

Test the login page ("/login"). A get request will show how to login to the server, and a post
request should return an auth token.
"""

import json
import pytest
import tornado.gen
import tornado.testing
import tornado.httpclient

from unittest.mock import MagicMock, patch

from src.routes import LoginPageHandler
from tests._base_test_cases import MyServerTestCase
from tests.fixtures import create_hashlib_fixture


class TestGetLoginPage(MyServerTestCase):
    """GET '/login'"""

    def test_response_code(self):
        """Should have an HTTP response code of 200."""
        response = self.fetch('/login')
        self.assertEqual(response.code, 200)

    def test_response_is_json(self):
        """Should have JSON encoded body."""
        response = self.fetch('/login')
        try:
            json.loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    def test_response_has_help_text(self):
        """Should have the login help text in the response body."""
        response = self.fetch('/login')
        self.assertEqual(type(response.body), bytes)
        self.assertIn(json.dumps(LoginPageHandler.get_description),
                      response.body.decode('utf-8'))

    def test_response_has_post_arguments_help(self):
        """Should have information about the post arguments in the response body."""
        response = self.fetch('/login')
        self.assertEqual(type(response.body), bytes)
        json_response = json.loads(response.body.decode('utf8'))
        self.assertIn('data', json_response)
        self.assertDictEqual(json_response['data'], LoginPageHandler.post_args)


@patch('src.routes.login.hashlib', create_hashlib_fixture(return_value='cake'))
class TestPostLoginPage(MyServerTestCase):
    """POST '/login'"""

    @tornado.testing.gen_test
    def test_no_arg_response_code(self):
        """Should have an HTTP response code of 400 when no arguments are supplied."""
        future = self.http_client.fetch(self.get_url('/login'), method='POST', body='')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_missing_username_response_code(self):
        """Should have an HTTP response code of 400 when "username" is missing."""

        # Test when "username" arg is missing.
        future = self.http_client.fetch(self.get_url('/login'), method='POST',
                                        body='password=password')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_missing_password_response_code(self):
        """Should have an HTTP response code of 400 when "password" is missing."""

        # Test when "password" arg is missing.
        future = self.http_client.fetch(self.get_url('/login'), method='POST',
                                        body='username=frank')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_username_does_not_exist_response_code(self):
        """Should have an HTTP response code of 400 when a user with "username" does not exist."""

        # Stub the server.db.execute function to return nothing. This way the check for a user with
        # "username" will fail and the method will error.
        async def return_no_user(*args, **kwargs):
            return return_no_user.mock(*args, **kwargs)

        return_no_user.mock = MagicMock(return_value=False)

        # Assign the stub to the server app instance
        self._app.db.execute = return_no_user

        future = self.http_client.fetch(self.get_url('/login'), method='POST',
                                        body='username=frank&password=password')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future

        # Assert the HTTP response code is 400
        self.assertEqual(error_info.value.code, 400)

        # Assert the mocked DB method was called once with certain params
        return_no_user.mock.assert_called_once_with('SELECT * FROM user WHERE username = ?',
                                                    'frank')

    @tornado.testing.gen_test
    def test_password_does_not_match_response_code(self):
        """Should have an HTTP response code of 401 when a user's password does not match."""

        # Stub the server.db.execute function to return a user. This way the check for a user with
        # "username" will return a user.
        async def return_a_user(*args, **kwargs):
            return return_a_user.mock(*args, **kwargs)

        return_a_user.mock = MagicMock(return_value=[(
            0,        # id
            'frank',  # username
            'test',   # password
        )])

        # Assign the stub to the server app instance
        self._app.db.execute = return_a_user

        future = self.http_client.fetch(self.get_url('/login'), method='POST',
                                        body='username=frank&password=test')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future

        # Assert the HTTP response code is 401
        self.assertEqual(error_info.value.code, 401)

    @tornado.testing.gen_test
    def test_success_response_code(self):
        """Should have an HTTP response code of 200 when password matches DB hash."""

        # Stub the server.db.execute function to return a user. This way the check for a user with
        # "username" will return a user.
        async def return_a_user(*args, **kwargs):
            return return_a_user.mock(*args, **kwargs)

        return_a_user.mock = MagicMock(return_value=[(
            0,  # id
            'frank',  # username
            'cake',  # password
        )])

        # Assign the stub to the server app instance
        self._app.db.execute = return_a_user

        # Stub the server.generate_auth_token method to return a predefined token. This way the
        # call to generate an auth token will succeed.
        stubbed_token = '<token>'
        async def return_a_token(*args, **kwargs):
            return return_a_token.mock(*args, **kwargs)

        return_a_token.mock = MagicMock(return_value=stubbed_token)

        # Assign the stub to the server app instance
        self._app.generate_auth_token = return_a_token

        response = yield self.http_client.fetch(self.get_url('/login'), method='POST',
                                                body='username=frank&password=cake')

        # Assert the HTTP response code is 200
        self.assertEqual(response.code, 200)
