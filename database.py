"""
/database.py

One thread to handle all calls to the database.
NOTE: I tried to get aioodbc working on my mac, but it was giving me too much hell.
"""

import asyncio
import sqlite3

from concurrent.futures import ThreadPoolExecutor

from util import utc_to_date, compare_utc_dates, now_as_utc


class DB(object):
    """Database connection in a single shared thread."""

    def __init__(self, database_file):
        """Constructor."""
        self.database_file = database_file
        self.db = sqlite3.connect(self.database_file, check_same_thread=False)
        self.register_functions()
        self.cur = self.db.cursor()
        self._db_envoy = ThreadPoolExecutor(max_workers=1)

    def register_functions(self):
        """Register some utility functions to the database."""
        self.db.create_function('now_as_utc', 0, now_as_utc)
        self.db.create_function('utc_to_date', 1, utc_to_date)
        self.db.create_function('compare_utc_dates', 3, compare_utc_dates)
        self.db.commit()

    async def execute(self, query, *args):
        """Execute the query and return all results."""
        await asyncio.wrap_future(self._db_envoy.submit(self.cur.execute, query, args))
        await asyncio.wrap_future(self._db_envoy.submit(self.db.commit))
        return await asyncio.wrap_future(self._db_envoy.submit(self.cur.fetchall))

    async def executescript(self, script):
        """Execute a SQL script."""
        return await asyncio.wrap_future(self._db_envoy.submit(self.cur.executescript, script))

    def close(self):
        """Close the connection to the database and the thread itself."""
        self.db.close()
        self._db_envoy.shutdown(wait=True)
