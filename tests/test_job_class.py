"""
tests/test_job_class.py

Test the scheduler's convenient "Job" class.
"""
import json

from unittest.mock import MagicMock

from src.scheduler import Job


class TestJob(object):
    """Job """

    def test_params_are_bound_on_init(self):
        """Should bind certain parameters on initialization."""
        id_ = 'id'
        user_id = 'user_id'
        name = 'name'
        type_id = 'type_id'
        data = '{}'
        schedule = 'schedule'
        done = 'done'
        last_ran = '1.00'
        date_created = 'date_created'
        date_updated = 'date_updated'
        job = Job(id_, user_id, name, type_id, data, schedule, done, last_ran, date_created,
                  date_updated)
        assert job.id is id_
        assert job.user_id is user_id
        assert job.name is name
        assert job.type_id is type_id
        assert job.data == json.loads(data)
        assert job.schedule is schedule
        assert job.done is done
        assert job.last_ran == float(last_ran)
        assert job.date_created is date_created
        assert job.date_updated is date_updated

    def test_data_is_json_parsed_on_init(self, monkeypatch):
        """Should parse data parameter as JSON on initialization."""

        # Stub json.loads
        json_loads = MagicMock(return_value='parsed json!')
        monkeypatch.setattr('src.scheduler.job.json.loads', json_loads)

        # Make a new Job object
        data = '{}'
        job = Job(None, None, None, None, data, None, None, None, None, None)

        # Assert data was passed into json.loads
        json_loads.assert_called_once_with(data)
        # Assert the bound data is the parsed json
        assert job.data == 'parsed json!'

    def test_run_once_if_schedule_startswith_once(self):
        """Should run once if schedule parameter is a string that starts with "once"."""
        schedule = 'once @ utc_timestamp'
        job = Job(None, None, None, None, '{}', schedule, None, None, None, None)
        assert job.run_once is True

    def test_not_run_once_if_schedule_not_string(self):
        """Should not run once if schedule parameter is not a string."""
        schedule = None
        job = Job(None, None, None, None, '{}', schedule, None, None, None, None)
        assert job.run_once is False

    def test_not_run_once_if_schedule_not_startswith_once(self):
        """Should not run once if schedule parameter is a string that does not start with "once"."""
        schedule = 'every 2 seconds'
        job = Job(None, None, None, None, '{}', schedule, None, None, None, None)
        assert job.run_once is False
