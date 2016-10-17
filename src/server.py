"""
src/server.py

Here's the server. Basically the "spine" of the project, where server routes are registered to page
handlers and the worker threads (such as the JobScheduler thread and the database thread) are
kicked off.
"""

import base64
import asyncio
import hashlib

from tornado.web import Application as TornadoApplication, HTTPError
from tornado.log import enable_pretty_logging
from tornado.httpserver import HTTPServer

from .database import DB
from .routes import IndexPageHandler, RegisterPageHandler, LoginPageHandler, JobPageHandler
from .utils import ConfigParser
from .utils.dates import now
from .scheduler import JobScheduler


class ServerApp(TornadoApplication):
    """Tornado server which maps routes to handlers and provides common resources to handlers."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        """ Constructor."""

        enable_pretty_logging()

        # Map routes to handlers
        routes_to_handlers = [
            (r'/', IndexPageHandler),
            (r'/register', RegisterPageHandler),
            (r'/login', LoginPageHandler),
            (r'/job', JobPageHandler),
        ]

        # Parse the server config file
        server_config = ConfigParser()

        # Application private key
        self.private_key = bytes(server_config.app_key, 'utf8')

        # Is development mode enabled?
        dev_enabled = True if str(server_config.app_env).lower() == 'development' else False

        # Define settings for the tornado app
        settings = {
            'autoreload': dev_enabled,
            'compress_response': True,
            'serve_traceback': dev_enabled,
            'app_env': server_config.app_env,
            'app_name': server_config.app_name,
            'app_port': server_config.port,
            'app_host': server_config.host,
        }

        # Call the parent class init function
        super().__init__(routes_to_handlers, **settings)

        # Initiate a shared connection to the database
        self.db = DB(server_config.db_file)

        # Initiate a threaded job scheduler

        work_queue = asyncio.Queue()
        self.scheduler = JobScheduler(work_queue, self.db, loop)

    def run(self):
        """Start the tornado server."""
        http_server = HTTPServer(self)
        http_server.listen(self.settings['app_port'])

    async def setup_db(self):
        """Create database schema if database is empty."""
        tables = await self.db.execute("SELECT name FROM sqlite_master WHERE type='table';")
        if len(tables) is 0:
            print('No tables found in database. Generating schema..')
            schema_sql = open('src/database/sql/schema.sql', 'r').read()
            await self.db.executescript(schema_sql)
            print('Schema generated successfully.')
        self.scheduler.start()

    async def generate_auth_token(self, user_id):
        """Generate an auth token for the user."""
        user = await self.db.execute('SELECT * FROM user WHERE id = ?;', user_id)
        if user:
            user = user[0]
            token_data = bytes((user[1] + ':' + ':' + str(now().timestamp())), 'utf8')
            token = hashlib.blake2b(digest_size=16, key=self.private_key)
            token.update(token_data)
            token = '{0}:{1}'.format(token.hexdigest(), user[1])
            token_base64 = base64.b64encode(bytes(token, 'utf8')).decode("utf-8")
            await self.db.execute('UPDATE user SET token=? WHERE id = ?;', token_base64, user_id)
            return token_base64
        else:
            raise HTTPError(401, 'Cannot locate user with id "{}"'.format(user_id))

    async def validate_auth_token(self, token_base64):
        """Parse an auth token and return the user database id."""
        try:
            token, username = base64.b64decode(token_base64).decode("utf-8").split(':')
            user = await self.db.execute('SELECT * FROM user WHERE username = ? AND token = ?;',
                                         username, token_base64)
            if user:
                user = user[0]
                return user[0]
            else:
                raise HTTPError(401, 'Could not find user to match auth token.')
        except:
            raise HTTPError(401, 'Invalid auth token.')
