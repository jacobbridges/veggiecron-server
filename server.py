#!/usr/bin/env python3
"""
/server.py

< Server description here... >
"""

import os
import json
import yaml
import base64
import asyncio
import hashlib
import tornado.httpserver

from tornado.web import RequestHandler, Application as TornadoApplication, HTTPError
from tornado.platform.asyncio import AsyncIOMainLoop
from yaml.scanner import ScannerError

from database import DB
from job_scheduler import Job, JobScheduler
from util import now, utc_to_date

# Create the event loop
# NOTE: This is necessary to bind the loop to the sqlite3 connection before starting the loop.
LOOP = asyncio.get_event_loop()


class ServerApp(TornadoApplication):
    """Tornado server which maps routes to handlers and provides common resources to handlers."""

    def __init__(self):
        """ Constructor."""

        # Map routes to handlers
        routes_to_handlers = [
            (r'/', IndexPageHandler),
            (r'/register', RegisterPageHandler),
            (r'/login', LoginPageHandler),
            (r'/job', JobPageHandler),
        ]

        # Parse the server config file
        server_config = None
        try:
            server_config = yaml.load(open('config.yaml', 'r'))
        except FileNotFoundError:
            current_path = os.getcwd() + '/'
            print('Error: Could not locate config.yaml at {}'.format(current_path))
            exit()
        except ScannerError as e:
            print(e)
            print('Error: Improper YAML in config.yaml.')
            exit()
        finally:
            if type(server_config) is not dict:
                print('Error: Unknown error while parsing config.yaml.')
                exit()

        # Application private key
        self.private_key = bytes(server_config['app']['key'], 'utf8')

        # Is development mode enabled?
        dev_enabled = True if str(server_config['app']['env']).lower() == 'development' else False

        # Define settings for the tornado app
        settings = {
            'autoreload': dev_enabled,
            'compress_response': True,
            'serve_traceback': dev_enabled,
            'app_env': server_config['app']['env'],
            'app_name': server_config['app']['name'],
            'app_port': server_config['app']['port'],
            'app_host': server_config['app']['host'],
        }

        # Call the parent class init function
        super().__init__(routes_to_handlers, **settings)

        # Initiate a shared connection to the database
        self.db = DB(server_config['db_file'])

        # Initiate a threaded job scheduler

        work_queue = asyncio.Queue()
        self.scheduler = JobScheduler(work_queue, self.db, LOOP)

    async def setup_db(self):
        """Create database schema if database is empty."""
        tables = await self.db.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print(tables)
        if len(tables) is 0:
            print('No tables found in database. Generating schema..')
            schema_sql = open('schema.sql', 'r').read()
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


class BasePageHandler(RequestHandler):
    """Base handler with common functions to make available to all other handlers."""

    def data_received(self, chunk):
        """Implement this method to handle streamed request data."""
        pass

    @property
    def db(self):
        return self.application.db

    @property
    def scheduler(self) -> JobScheduler:
        return self.application.scheduler

    async def get_cursor(self):
        return await self.application.db.cursor()

    async def validate_auth_token(self, token_base64):
        return self.application.validate_auth_token(token_base64)

    async def generate_auth_token(self, user_id):
        return self.application.generate_auth_token(user_id)


class IndexPageHandler(BasePageHandler):
    """Page handler for index ('/') route."""

    def get(self):
        self.write(json.dumps(self.application.settings))


class RegisterPageHandler(BasePageHandler):
    """Page handler for register ('/register') route."""

    def get(self):
        self.write(json.dumps({
            'id': 'success',
            'description': 'Send a POST request to this endpoint with a "username" and "password" '
                           'argument to register a user.',
            'data': {},
        }))

    async def post(self):
        # Check all post arguments were supplied
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        if any([username is None, password is None]):
            raise HTTPError(400, 'Both username and password are required to register.')

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
        self.write(json.dumps({
            'id': 'success',
            'description': 'You are registered as "{}"! Proceed to login.'.format(username),
            'data': {
                'username': username,
                'date_created': time_now,
                'date_updated': time_now,
            }
        }))


class LoginPageHandler(BasePageHandler):
    """Page handler for login ('/login') route."""

    def get(self):
        self.write(json.dumps({
            'id': 'success',
            'description': 'Send a POST request to this endpoint with a "username" and "password"'
                           'arguments to retrieve an auth token.',
            'data': {}
        }))

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
            return self.write(json.dumps({
                'id': 'success',
                'description': 'You have successfully generated an auth token! Check the data key.',
                'data': {
                    'token': token
                }
            }))
        else:
            raise HTTPError(401, 'Incorrect password!')


class JobPageHandler(BasePageHandler):

    async def get(self):
        # Check for auth token
        auth_token = self.request.headers.get('X-Auth-Token', None)
        user_id = await self.application.validate_auth_token(auth_token)

        job_name = self.get_query_argument('name', None)
        if job_name is None:

            # Get all jobs for user
            jobs = await self.db.execute("SELECT * FROM job WHERE user_id = ?;", user_id)
            job_types = await self.db.execute("SELECT id, name FROM job_type;")
            job_types = {k: v for k, v in job_types}
            return self.write(json.dumps({
                'id': 'success',
                'description': 'List all jobs for the given user.',
                'data': {
                    'jobs': [
                        {
                            'name': j[2],
                            'type': job_types[j[3]],
                            'data': j[4],
                            'schedule': j[5],
                            'last_ran': j[7],
                            'done': True if j[6] is 1 else False
                        } for j in jobs
                    ],
                }
            }))

        else:

            # Get the job by name
            job = await self.db.execute("SELECT * FROM job WHERE user_id = ? AND name = ?",
                                        user_id, job_name)
            if len(job) == 0:
                raise HTTPError(404, 'Job "{}" does not exist for the current user.'
                                .format(job_name))

            job = job[0]
            job_types = await self.db.execute("SELECT id, name FROM job_type;")
            job_types = {k: v for k, v in job_types}
            job_results = await self.db.execute("SELECT id, result, date_created FROM job_result "
                                                "WHERE job_id = ? ORDER BY id DESC LIMIT 25",
                                                job[0])

            return self.write(json.dumps({
                'id': 'success',
                'description': 'Information for job "{}"'.format(job_name),
                'data': {
                    'job': {
                        'name': job_name,
                        'type': job_types[job[3]],
                        'data': job[4],
                        'schedule': job[5],
                        'last_ran': job[7],
                        'done': True if job[6] is 1 else False
                    },
                    'job_runs': [{'result': r[1], 'timestamp': utc_to_date(float(r[2])).isoformat()}
                                 for r in job_results]
                }
            }))

    async def post(self):
        # Check for auth token
        auth_token = self.request.headers.get('X-Auth-Token', None)
        user_id = await self.application.validate_auth_token(auth_token)

        # Check all post arguments are supplied
        job_name = self.get_argument('name', None)
        job_type = self.get_argument('type', None)
        job_data = self.get_argument('data', None)
        job_schedule = self.get_argument('schedule', None)
        if any([job_name is None, job_type is None, job_data is None, job_schedule is None]):
            raise HTTPError(400, 'Must include the following form data: "name", "type", "data", '
                                 '"schedule"')

        # Create a job from the post data
        job_type_id = await self.db.execute("SELECT * FROM job_type WHERE name = ?", job_type)
        if job_type_id:
            job_type_id = job_type_id[0][0]
            time_now = now().timestamp()
            await self.db.execute('INSERT INTO job (id, user_id, name, type_id, data, schedule, '
                                  'date_created, date_updated) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);',
                                  user_id, job_name, job_type_id, job_data, job_schedule,
                                  time_now, time_now)
            job = await self.db.execute('SELECT * FROM job WHERE user_id = ? AND name = ?',
                                        user_id, job_name)
            job = job[0]
            job_obj = Job(*job)
            await self.scheduler.work_queue.put(job_obj)
            return self.write(json.dumps({
                'id': 'success',
                'description': 'Successfully created {0} job: "{1}"'.format(job_type, job_name),
                'data': {
                    'name': job_name,
                    'type': job_type,
                    'data': job_data,
                    'schedule': job_schedule,
                    'date_created': time_now,
                    'date_updated': time_now,
                }
            }))
        else:
            raise HTTPError(400, 'Job type "{}" does not exist.'.format(job_type))


def main(web_app):

    # Start the server
    http_server = tornado.httpserver.HTTPServer(web_app)
    http_server.listen(web_app.settings['app_port'])


if __name__ == '__main__':

    # Create a tornado IOLoop that corresponds to the asyncio event loop
    AsyncIOMainLoop().install()

    # Run the main app
    app = ServerApp()
    LOOP.create_task(app.setup_db())
    LOOP.call_soon(main, app)

    # Start the asyncio event loop
    try:
        LOOP.run_forever()
    finally:
        app.db.close()
