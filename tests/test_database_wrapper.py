"""
tests/test_database_wrapper.py

Test the database wrapper which runs in a separate thread and handles all calls to the database.
"""
import pytest

from unittest import TestCase
from unittest.mock import MagicMock, patch

from src.database import DB

from tests.fixtures import create_sqlite3_db, create_sqlite3_cursor


class TestDatabaseWrapper(TestCase):
    """Database wrapper"""

    @patch('src.database.DB.register_functions', MagicMock())
    @patch('src.database.connection.ThreadPoolExecutor', MagicMock())
    @patch('src.database.connection.sqlite3.connect')
    def test_create_connection_on_init(self, connect_stub):
        """Should create a connection to the database on initialization."""

        # Initialize the database wrapper class
        DB('filename')

        # Assert the stubbed connection was called, which should connect to the database
        connect_stub.assert_called_once_with('filename', check_same_thread=False)

    @patch('src.database.connection.ThreadPoolExecutor', MagicMock())
    @patch('src.database.connection.sqlite3.connect')
    def test_register_three_functions_on_init(self, connect_stub):
        """Should register three custom functions to the database on initialization."""

        # Advanced fixture should be returned from connect_stub
        db_stub = create_sqlite3_db(create_sqlite3_cursor())
        connect_stub.return_value = db_stub

        # Initialize the database wrapper class
        DB('filename')

        # Assert the custom functions were registered
        self.assertEqual(db_stub.create_function.call_count, 3)
        # Assert the custom functions were committed to the database
        db_stub.commit.assert_called_once()

    @patch('src.database.DB.register_functions', MagicMock())
    @patch('src.database.connection.ThreadPoolExecutor', MagicMock())
    @patch('src.database.connection.sqlite3.connect')
    def test_create_cursor_on_init(self, connect_stub):
        """Should create a cursor and bind it on initialization."""

        # Advanced fixture should be returned from connect_stub
        cursor_stub = create_sqlite3_cursor()
        db_stub = create_sqlite3_db(cursor_stub)
        connect_stub.return_value = db_stub

        # Initialize the database wrapper class
        db = DB('filename')

        # Assert the cursor was created
        db_stub.cursor.assert_called_once()
        # Assert the cursor was bound to the object
        self.assertEqual(db.cur, cursor_stub, 'The cursor should have been bound to the db wrapper '
                                              'object.')

    @patch('src.database.DB.register_functions', MagicMock())
    @patch('src.database.connection.sqlite3.connect', MagicMock())
    @patch('src.database.connection.ThreadPoolExecutor')
    def test_create_thread_on_init(self, threadpool_stub):
        """Should create a "ThreadPool" with one thread and bind it on initialization."""
        threadpool_stub.return_value = 'thread'

        # Initialize the database wrapper class
        db = DB('filename')

        # Assert the threadpool was started with one thread
        threadpool_stub.assert_called_once_with(max_workers=1)
        # Assert the threadpool was bound to the object
        self.assertEqual(db._db_envoy, 'thread')
