"""
tests/fixtures/py

Common fixtures shared among tests are stored here.
"""

from unittest import mock


def create_db_fixture():
    return mock.MagicMock()


def create_job_scheduler_fixture():
    return mock.MagicMock()


def create_config_parser_fixture():
    fixture = mock.MagicMock()
    fixture.app_env = 'development'
    fixture.app_name = 'veggiecron-server'
    fixture.app_key = 'app-key'
    fixture.host = '0.0.0.0'
    fixture.port = '8118'
    fixture.db_file = 'sqlite3.db'
    return fixture
