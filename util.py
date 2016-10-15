"""
/util.py

Helpful functions that only provide utility for the rest of the project.
"""

import pytz

from datetime import datetime


def now():
    return datetime.now(tz=pytz.timezone('US/Central'))


def now_as_utc():
    return now().timestamp()


def utc_to_date(utc: float):
    return datetime.fromtimestamp(utc, tz=pytz.timezone('US/Central'))


def compare_utc_dates(utc1: float, op: str, utc2: float):
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
