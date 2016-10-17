"""
src/routes/login.py

Login "/login" route for all HTTP methods.
"""

import hashlib

from tornado.web import HTTPError

from ._base import BasePageHandler


class LoginPageHandler(BasePageHandler):
    """Page handler for login ('/login') route."""

    def get(self):
        self.write({
            'id': 'success',
            'description': 'Send a POST request to this endpoint with a "username" and "password"'
                           'arguments to retrieve an auth token.',
            'data': {}
        })

    async def post(self):
        # Check all post arguments were supplied
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        if any([username is None, password is None]):
            raise HTTPError(400, 'Both username and password are required to retrieve a token.')

        # Check that the username is an alphanumeric string
        if not str.isalnum(username):
            raise HTTPError(400, 'Username must be an alphanumeric string.')

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
