"""
tests/fixtures/py

Common fixtures shared among tests are stored here.
"""
import json

from unittest import mock


####################################################################################################
# Fixture Functions

def create_fixture_func(*return_values):
    """Return a fixture function with different return values for each call."""
    return mock.MagicMock(side_effects=return_values)


def create_config_parser_fixture():
    """Return a mocked src.utils.ConfigParser object."""
    fixture = mock.MagicMock()
    fixture.app_env = 'development'
    fixture.app_name = 'veggiecron-server'
    fixture.app_key = 'app-key'
    fixture.host = '0.0.0.0'
    fixture.port = '8118'
    fixture.db_file = 'sqlite3.db'
    return fixture


def create_hashlib_fixture(return_value=None):
    """Return a mocked hashlib object."""
    fixture = mock.MagicMock()
    deep_fixture = mock.MagicMock()
    deep_fixture.hexdigest = lambda: return_value
    fixture.sha256 = mock.MagicMock(return_value=deep_fixture)
    return fixture


def create_sqlite3_cursor(*return_values):
    """Return a mocked sqlite3 db cursor."""
    fixture = mock.MagicMock()
    fixture.execute = mock.MagicMock()
    fixture.executescript = mock.MagicMock()
    fixture.fetchall = mock.MagicMock(side_effects=return_values)
    return fixture


def create_sqlite3_db(cursor):
    """Return a mocked db object returned from sqlite3.connect."""
    fixture = mock.MagicMock()
    fixture.cursor = mock.MagicMock(return_value=cursor)
    fixture.create_function = mock.MagicMock()
    fixture.commit = mock.MagicMock()
    return fixture


####################################################################################################
# Fixture Variables

db_response_jobs_with_type = [
    (
        1,
        1,
        'job_1',
        1,
        json.dumps({"url": "http://requestb.in/1015j8y1",
                    "number_of_clones": 0,
                    "enable_shadows": True,
                    "verb": "GET"}),
        'every 10 seconds',
        0,
        '1485218461.30805',
        '1485218461.30805',
        '1485218461.30805',
        'http'
    ),
    (
        2,
        1,
        'job_2',
        1,
        json.dumps({"url": "http://requestb.in/1015j8y1",
                    "number_of_clones": 0,
                    "enable_shadows": True,
                    "verb": "GET"}),
        'every 2 minutes',
        0,
        '1485218461.30805',
        '1485218461.30805',
        '1485218461.30805',
        'http'
    ),
]

db_response_job_results = [
    (1, '{"code": 200, "body": "ok"}', '1485236321.08443'),
    (2, '{"code": 200, "body": "ok"}', '1485236331.09924'),
    (3, '{"code": 200, "body": "ok"}', '1485236405.69861'),
]

db_response_job_type = [
    (1, 'http', '{"url":{"type":"string","description":"URL prepended with \'http://\'."},"number_'
                'of_clones":{"type":"number","description":"Don\'t just make the request one time '
                'on every interval. Do it X number of times."},"verb":{"type":"string",'
                '"description":"HTTP verbs: [GET, POST, PUT, DELETE]"},"enable_shadows":{"type":'
                '"boolean","description":"Turn on shadows if you want this job to run again even '
                'if the last run is still active. (For long running requests.)"}}'),
]

db_response_job = [
    (
        1,
        1,
        'job_1',
        1,
        json.dumps({"url": "http://requestb.in/1015j8y1",
                    "number_of_clones": 0,
                    "enable_shadows": True,
                    "verb": "GET"}),
        'every 10 seconds',
        0,
        '1485218461.30805',
        '1485218461.30805',
        '1485218461.30805',
    )
]

request_create_job_params = {
    'name': 'job_1',
    'type': 'http',
    'data': json.dumps({
        'url': 'http://requestb.in/1015j8y1',
        'number_of_clones': 0,
        'enable_shadows': True,
        'verb': 'GET'
    }),
    'schedule': 'every minute'
}
