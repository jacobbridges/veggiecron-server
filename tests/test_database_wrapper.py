"""
tests/test_database_wrapper.py

Test the database wrapper which runs in a separate thread and handles all calls to the database.
"""
import pytest
import asyncio

from unittest.mock import MagicMock, call

from src.database import DB

from tests import fixtures


class TestDatabaseWrapper(object):
    """Database wrapper"""

    def test_create_connection_on_init(self, monkeypatch):
        """Should create a connection to the database on initialization."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())
        connect_stub = MagicMock()
        monkeypatch.setattr('src.database.connection.sqlite3.connect', connect_stub)

        # Initialize the database wrapper class
        DB('filename')

        # Assert the stubbed connection was called, which should connect to the database
        connect_stub.assert_called_once_with('filename', check_same_thread=False)

    def test_register_three_functions_on_init(self, monkeypatch):
        """Should register three custom functions to the database on initialization."""
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())
        connect_stub = MagicMock()
        monkeypatch.setattr('src.database.connection.sqlite3.connect', connect_stub)

        # Advanced fixture should be returned from connect_stub
        db_stub = fixtures.create_sqlite3_db(fixtures.create_sqlite3_cursor())
        connect_stub.return_value = db_stub

        # Initialize the database wrapper class
        DB('filename')

        # Assert three custom functions were registered
        assert db_stub.create_function.call_count is 3
        # Assert the custom functions were committed to the database
        db_stub.commit.assert_called_once()

    def test_create_cursor_on_init(self, monkeypatch):
        """Should create a cursor and bind it on initialization."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())
        connect_stub = MagicMock()
        monkeypatch.setattr('src.database.connection.sqlite3.connect', connect_stub)

        # Advanced fixture should be returned from connect_stub
        cursor_stub = fixtures.create_sqlite3_cursor()
        db_stub = fixtures.create_sqlite3_db(cursor_stub)
        connect_stub.return_value = db_stub

        # Initialize the database wrapper class
        db = DB('filename')

        # Assert the cursor was created
        db_stub.cursor.assert_called_once()
        # Assert the cursor was bound to the object
        assert db.cur == cursor_stub, 'The cursor should have been bound to the db wrapper object.'

    def test_create_thread_on_init(self, monkeypatch):
        """Should create a "ThreadPool" with one thread and bind it on initialization."""
        threadpool_stub = MagicMock()
        threadpool_stub.return_value = 'thread'
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', threadpool_stub)
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())

        # Initialize the database wrapper class
        db = DB('filename')

        # Assert the threadpool was started with one thread
        threadpool_stub.assert_called_once_with(max_workers=1)
        # Assert the threadpool was bound to the object
        assert db._db_envoy == 'thread'

    @pytest.mark.asyncio
    async def test_proxy_query_and_args_on_execute(self, monkeypatch):
        """Should submit query and query arguments to the thread executor."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Create a future for the thread executor submit stub to return
        submit_future = asyncio.Future()
        submit_future.set_result(None)

        # Initialize the database wrapper
        db = DB('filename')

        # Stub the result of the thread executor submit method
        db._db_envoy.submit.return_value = submit_future

        # Execute a query
        await db.execute('some sql', 1, 2, 3)

        # Assert the query submission was sent to the threadpool
        assert call(db.cur.execute, 'some sql', (1, 2, 3)) in db._db_envoy.submit.call_args_list

    @pytest.mark.asyncio
    async def test_commit_on_execute(self, monkeypatch):
        """Should run a "db.commit" on query execution."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Create a future for the thread executor submit stub to return
        submit_future = asyncio.Future()
        submit_future.set_result(None)

        # Initialize the database wrapper
        db = DB('filename')

        # Stub the result of the thread executor submit method
        db._db_envoy.submit.return_value = submit_future

        # Execute a query
        await db.execute('some sql', 1, 2, 3)

        # Assert the query submission was sent to the threadpool
        assert call(db.db.commit) in db._db_envoy.submit.call_args_list

    @pytest.mark.asyncio
    async def test_return_results_after_execute(self, monkeypatch):
        """Should return the results of the query (if any)."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Create a future for the thread executor submit stub to return
        result = 'query result'
        submit_future = asyncio.Future()
        submit_future.set_result(result)

        # Initialize the database wrapper
        db = DB('filename')

        # Stub the result of the thread executor submit method
        db._db_envoy.submit.return_value = submit_future

        # Execute a query
        awaited_result = await db.execute('some sql', 1, 2, 3)

        # Assert that db.execute returns the result of the query
        assert awaited_result is result
        # Assert the call to fetch results was made
        assert call(db.cur.fetchall) in db._db_envoy.submit.call_args_list

    @pytest.mark.asyncio
    async def test_proxy_script_on_executescript(self, monkeypatch):
        """Should submit the script to the thread on executescript."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Create a future for the thread executor submit stub to return
        submit_future = asyncio.Future()
        submit_future.set_result(None)

        # Initialize the database wrapper
        db = DB('filename')

        # Stub the result of the thread executor submit method
        db._db_envoy.submit.return_value = submit_future

        # Execute a script
        await db.executescript('some script')

        # Assert the script submission was sent to the threadpool
        assert call(db.cur.executescript, 'some script') in db._db_envoy.submit.call_args_list

    @pytest.mark.asyncio
    async def test_return_results_on_executescript(self, monkeypatch):
        """Should return the result of executescript from the thread."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Create a future for the thread executor submit stub to return
        result = 'script result'
        submit_future = asyncio.Future()
        submit_future.set_result(result)

        # Initialize the database wrapper
        db = DB('filename')

        # Stub the result of the thread executor submit method
        db._db_envoy.submit.return_value = submit_future

        # Execute a script
        script_result = await db.executescript('some script')

        # Assert the response from executescript matches the response from the thread
        assert result is script_result

    def test_db_close_on_close(self, monkeypatch):
        """Should close the database connection on close."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Initialize the database wrapper
        db = DB('filename')

        # Close the object
        db.close()

        # Assert that the database's internal database connection was closed
        db.db.close.assert_called_once()

    def test_threadpool_shutdown_on_close(self, monkeypatch):
        """Should shutdown the ThreadPoolExecutor on close."""
        monkeypatch.setattr('src.database.DB.register_functions', MagicMock())
        monkeypatch.setattr('src.database.connection.sqlite3.connect', MagicMock())
        monkeypatch.setattr('src.database.connection.ThreadPoolExecutor', MagicMock())

        # Initialize the database wrapper
        db = DB('filename')

        # Close the object
        db.close()

        # Assert that the ThreadPoolExecutor was shutdown
        db._db_envoy.shutdown.assert_called_once_with(wait=True)
