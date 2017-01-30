"""
src/routes/register.py

Register "/register" route for all HTTP methods.
"""

import hashlib

from tornado.web import HTTPError, MissingArgumentError

from ._base import BasePageHandler
from ..utils.dates import now


class RegisterPageHandler(BasePageHandler):
    """Page handler for register ('/register') route."""

    get_description = 'Send a POST request to /register to create a user. Check "data" which ' \
                      'arguments need to be sent with the request.'
    post_args = {
        'username': {
            'description': 'Your username must be an alphanumeric string.',
            'type': 'text',
            'required': True,
        },
        'password': {
            'description': 'Your password is not saved to the server.',
            'type': 'text',
            'required': True,
        }
    }

    def get(self):
        self.write({
            'id': 'success',
            'description': self.get_description,
            'data': self.post_args,
        })

    async def post(self):
        # Check all post arguments were supplied
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        if all([username is None, password is None]):
            raise MissingArgumentError('Username and Password')
        if username is None:
            raise MissingArgumentError('Username')
        if password is None:
            raise MissingArgumentError('Password')

        # Check that the username is an alphanumeric string
        if not str.isalnum(username):
            raise HTTPError(400, 'Username must be an alphanumeric string.')

        # Check that there isn't already a user with the same username
        user = await self.db.execute("SELECT * FROM user WHERE username = ?;", username)
        if user:
            raise HTTPError(400, 'That username is already taken.')

        # Register the user
        password = hashlib.sha256(bytes(password, encoding='utf8')).hexdigest()
        time_now = now().timestamp()
        await self.db.execute("INSERT INTO user (id, username, password, date_created, "
                              "date_updated) VALUES (NULL, ?, ?, ?, ?);", username, password,
                              time_now, time_now)
        self.write({
            'id': 'success',
            'description': 'You are registered as "{}"! Proceed to login.'.format(username),
            'data': {
                'username': username,
                'date_created': time_now,
                'date_updated': time_now,
            }
        })
