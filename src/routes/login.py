"""
src/routes/login.py

Login "/login" route for all HTTP methods.
"""

import hashlib

from tornado.web import HTTPError, MissingArgumentError

from ._base import BasePageHandler
from .register import RegisterPageHandler


class LoginPageHandler(BasePageHandler):
    """Page handler for login ('/login') route."""

    get_description = 'Send a POST request to this endpoint with "username" and "password" ' \
                      'arguments to retrieve an auth token.'

    post_args = RegisterPageHandler.post_args

    def get(self):
        self.write({
            'id': 'success',
            'description': self.get_description,
            'data': self.post_args
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

        # Search for a user with the given username
        user = await self.db.execute("SELECT * FROM user WHERE username = ?", username)
        if not user:
            raise HTTPError(400, 'A user with that username does not exist.')
        user = user[0]

        # Check the password against the hashed password
        if user[2] == hashlib.sha256(bytes(password, encoding='utf8')).hexdigest():
            token = await self.application.generate_auth_token(user[0])
            return self.write({
                'id': 'success',
                'description': 'You have successfully generated an auth token! Check the data key.',
                'data': {
                    'token': token
                }
            })
        else:
            raise HTTPError(401, 'Incorrect password!')
