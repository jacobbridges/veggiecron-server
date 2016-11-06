"""
tests/fixtures/py

Common fixtures shared among tests are stored here.
"""

from unittest import mock


def create_db_fixture():
    """Return a mocked src.database.DB object."""
    return mock.MagicMock()


def create_job_scheduler_fixture():
    """Return a mocked src.scheduler.JobScheduler object."""
    return mock.MagicMock()


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
