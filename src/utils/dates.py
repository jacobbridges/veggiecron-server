"""
src/utils/dates.py

This file contains utility functions for handling dates in this project. SQLite doesn't support
any date or time types by default, so I am using UTC timestamps.
"""

import pytz

from datetime import datetime


def now(as_utc=False):
    """Get the current time with correct timezone."""
    if as_utc:
        return datetime.now(tz=pytz.timezone('US/Central')).timestamp()
    else:
        return datetime.now(tz=pytz.timezone('US/Central'))


def utc_to_date(utc: float):
    """Translate a UTC number to a Python datetime."""
    return datetime.fromtimestamp(utc, tz=pytz.timezone('US/Central'))


def compare_utc_dates(utc1: float, op: str, utc2: float):
    """Compare two UTC dates. This function is meant to be registered by SQLite3."""
    utcdate1 = utc_to_date(utc1)
    utcdate2 = utc_to_date(utc2)
    if op == '==':
        return utcdate1 == utcdate2
    if op == '!=':
        return utcdate1 != utcdate2
    if op == '>=':
        return utcdate1 >= utcdate2
    if op == '<=':
        return utcdate1 <= utcdate2
    if op == '>':
        return utcdate1 > utcdate2
    if op == '<':
        return utcdate1 < utcdate2
    raise ValueError('Expecting one of the following operators: [==, !=, >=, <=, >, <]')
