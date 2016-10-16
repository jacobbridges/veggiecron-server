"""
src/scheduler/parser.py

Parse job schedule strings into date of next job execution.
"""

from datetime import timedelta

from ..utils.dates import utc_to_date


schedule_string_syntax = """
Schedule string must be one of the following formats:
  * "every hour"
  * "every 2 hours"
  * "every 2 minutes"
  * "every 10 seconds"
  * "every day @ 13:00"
  * "every 30 days @ 7:30"
  * "once @ <utc-timestamp>" """


class ParseError(ValueError):
    """Custom exception for parse function."""
    pass


def parse(schedule_string: str, last_ran: float):
    """Parse a schedule string into a Python datetime of next scheduled execution."""

    assert isinstance(schedule_string, str)
    assert isinstance(last_ran, float)
    last_ran = utc_to_date(last_ran)

    units = ('day', 'days', 'hour', 'hours', 'minute', 'minutes', 'second', 'seconds')
    digit = None
    unit = None

    pieces = schedule_string.split(' ')
    if len(pieces) < 2:
        raise ParseError(schedule_string_syntax)

    if pieces[0] == 'every':

        if len(pieces) == 2:
            digit = 1
            unit = pieces[1]

        if len(pieces) == 3:
            try:
                digit = int(pieces[1])
                unit = pieces[2]
            except ValueError:
                raise ParseError(schedule_string_syntax)

        if unit not in units:
            raise ParseError(schedule_string_syntax)

        if unit in ('day', 'days'):

            if '@' in schedule_string and len(pieces) >= 4:
                time = pieces[3].strip()

            else:
                time = '00:00'  # Run at midnight if no "@ <time>" is specified

            try:
                hour, minute = (int(time[:2]), int(time[-2:]))
            except ValueError:
                raise ParseError(schedule_string_syntax)

            next_run = last_ran + timedelta(days=+digit)
            next_run.hour = hour
            next_run.minute = minute
            next_run.second = 0

            return next_run

        if unit in ('hour', 'hours'):
            return last_ran + timedelta(hours=+digit)

        if unit in ('minute', 'minutes'):
            return last_ran + timedelta(minutes=+digit)

        if unit in ('second', 'seconds'):
            return last_ran + timedelta(seconds=+digit)

    elif pieces[0] == 'once':

        if len(pieces) != 3 or pieces[1] != '@':
            raise ParseError(schedule_string_syntax)

        try:
            time_to_run = utc_to_date(float(pieces[2]))
        except ValueError:
            raise ParseError(schedule_string_syntax)

        return time_to_run

    else:
        raise ParseError(schedule_string_syntax)
