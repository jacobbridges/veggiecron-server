"""
src/scheduler/job.py

The Job class. (for classy jobs :tophat:)
"""

import json


class Job(object):
    """Wrapper around a job, providing convenience functions and typing."""

    def __init__(self, id_=None, user_id=None, name=None, type_id=None, data=None, schedule=None,
                 done=None, last_ran=None, date_created=None, date_updated=None):
        """Constructor."""
        self.id = id_
        self.user_id = user_id
        self.name = name
        self.type_id = type_id
        self.data = json.loads(data)
        self.schedule = schedule
        self.done = done
        self.last_ran = float(last_ran) if last_ran is not None else None
        self.date_created = date_created
        self.date_updated = date_updated

        if isinstance(self.schedule, str) and self.schedule.startswith('once'):
            self.run_once = True
        else:
            self.run_once = False
