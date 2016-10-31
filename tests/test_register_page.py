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

from unittest.mock import MagicMock

from src.routes.register import RegisterPageHandler
from tests._base_test_cases import MyServerTestCase


class TestGetRegisterPage(MyServerTestCase):
    """GET '/register'"""

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
    """POST '/register'"""

    @tornado.testing.gen_test
    def test_no_arg_response_code(self):
        """Should have an HTTP response code of 400 when no arguments are supplied."""
        future = self.http_client.fetch(self.get_url('/register'), method='POST', body='')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @pytest.mark.skip(reason='Helpful errors have not been implemented yet.')
    @tornado.testing.gen_test
    def test_no_arg_response(self):
        """Should have a helpful hint in the response when no arguments are supplied."""
        future = self.http_client.fetch(self.get_url('/register'), method='POST', body='')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertIn('Both username and password are required to register.', str(error_info.value))

    @tornado.testing.gen_test
    def test_missing_arg_response_code(self):
        """Should have an HTTP response code of 400 when "username" is missing."""

        # Test when "username" arg is missing.
        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='password=franky')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

        # Test when "password" arg is missing.
        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='username=frank')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_username_not_alphanumeric(self):
        """Should have an HTTP response code of 400 when "username" is not alphanumeric."""
        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='username=kev-g&password=123')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_username_already_exists(self):
        """Should have an HTTP response code of 400 when "username" already exists."""

        # Stub the server.db.execute function to return a user. This way the check for a user
        # with the same name will fail and the method will error.
        async def return_fake_user(*args, **kwargs):
            return return_fake_user.mock(*args, **kwargs)
        return_fake_user.mock = MagicMock(return_value=True)

        # Assign the stub to the server app instance
        self._app.db.execute = return_fake_user

        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='username=frank&password=franky')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future

        # Assert the HTTP response code is 400
        self.assertEqual(error_info.value.code, 400)

        # Assert the mocked DB method was called once with certain params
        return_fake_user.mock.assert_called_once_with('SELECT * FROM user WHERE username = ?;',
                                                      'frank')

    @tornado.testing.gen_test
    def test_success_response_code(self):
        """Should have an HTTP response code of 200 when args are correct."""

        # Stub the server.db.execute function to on first call return False (the check for
        # another user with same name) and on second call return True (for creating the new user
        # in the database)
        async def mocked_execute(*args, **kwargs):
            return mocked_execute.mock(*args, **kwargs)
        mocked_execute.mock = MagicMock(side_effect=[False, True])

        # Assign the stub to the server app instance
        self._app.db.execute = mocked_execute

        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='username=frank&password=franky')
        response = yield future

        # Assert the HTTP response code is 200
        self.assertEqual(response.code, 200)

        # Assert the mocked DB method was called as expected
        self.assertEqual(mocked_execute.mock.call_count, 2)

    @tornado.testing.gen_test
    def test_success_response_is_json(self):
        """Should have JSON encoded success response body."""

        # Stub the server.db.execute function to on first call return False (the check for
        # another user with same name) and on second call return True (for creating the new user
        # in the database)
        async def mocked_execute(*args, **kwargs):
            return mocked_execute.mock(*args, **kwargs)

        mocked_execute.mock = MagicMock(side_effect=[False, True])

        # Assign the stub to the server app instance
        self._app.db.execute = mocked_execute

        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='username=frank&password=franky')
        response = yield future
        try:
            json.loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    @tornado.testing.gen_test
    def test_success_response_has_username(self):
        """Should have the username in the success response body."""

        # Stub the server.db.execute function to on first call return False (the check for
        # another user with same name) and on second call return True (for creating the new user
        # in the database)
        async def mocked_execute(*args, **kwargs):
            return mocked_execute.mock(*args, **kwargs)

        mocked_execute.mock = MagicMock(side_effect=[False, True])

        # Assign the stub to the server app instance
        self._app.db.execute = mocked_execute

        future = self.http_client.fetch(self.get_url('/register'), method='POST',
                                        body='username=frank&password=franky')
        response = yield future
        self.assertIn('frank', response.body.decode('utf-8'))
