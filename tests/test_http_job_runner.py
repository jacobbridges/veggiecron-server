"""
tests/test_http_job_runner.py

Test the the job runner which handles all http jobs.
"""
import asyncio
import pytest

from unittest.mock import MagicMock


@pytest.fixture
def httpjobrunner():
    from src.scheduler.job_runners.http import HTTPJobRunner
    return HTTPJobRunner


@pytest.fixture
def job():
    obj = MagicMock()
    obj.id = 1
    obj.user_id = 1
    obj.name = 'job1'
    obj.type_id = 1
    obj.data = {'number_of_clones': 1, 'enable_shadows': False}
    obj.schedule = 'every minute'
    obj.done = 0
    obj.last_ran = None
    obj.date_created = None
    obj.date_updated = None
    obj.run_once = False
    return obj


class TestHttpJobRunner(object):
    """HTTP JobRunner"""

    def test_bind_http_client_to_class_on_load_class(self, monkeypatch, httpjobrunner):
        """Should instantiate and bind an async http client to the class on load_class()"""
        async_http_client_stub = MagicMock()
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient',
                            async_http_client_stub)
        httpjobrunner.load_class(MagicMock(), MagicMock())
        async_http_client_stub.assert_called_once_with(max_clients=httpjobrunner.max_open_requests)

    def test_bind_db_to_class_on_load_class(self, monkeypatch, httpjobrunner):
        """Should bind db object parameter to the class on load_class()"""
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        db_stub = MagicMock()
        httpjobrunner.load_class(db_stub, MagicMock())
        assert httpjobrunner.db is db_stub

    def test_bind_scheduler_queue_to_class_on_load_class(self, monkeypatch, httpjobrunner):
        """Should bind scheduler queue parameter to the class on load_class()"""
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        scheduler_queue_stub = MagicMock()
        httpjobrunner.load_class(MagicMock(), scheduler_queue_stub)
        assert httpjobrunner.scheduler_queue is scheduler_queue_stub

    def test_do_nothing_on_load(self, httpjobrunner):
        """Should do nothing on instance load()"""
        assert httpjobrunner().load() is None

    @pytest.mark.asyncio
    async def test_delay_on_run(self, monkeypatch, httpjobrunner, job):
        """Should delay the execution of run() if delay parameter is greater than zero."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub the sleep coroutine with a mock that returns a future
        sleep_stub = MagicMock()
        sleep_future = asyncio.Future()
        sleep_future.set_result(None)
        sleep_stub.return_value = sleep_future
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.sleep', sleep_stub)

        # Prepare the job runner
        httpjobrunner.load_class(MagicMock(), MagicMock())
        runner = httpjobrunner()

        # Run the job with some fake data, but be sure the delay is above 0
        delay = 1
        await runner.run(job, delay)

        # Assert that asyncio.sleep was called with the delay
        sleep_stub.assert_called_once_with(delay)
        # Assert that sleep was awaited properly (the future finished)
        assert sleep_future.done() is True

    @pytest.mark.asyncio
    async def test_make_requests_for_num_of_clones_on_run(self, monkeypatch, httpjobrunner, job):
        """Should "queue up" x HTTP requests on run(), where x is the job's "number_of_clones"."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub asyncio.gather so I can test that it was called with a number of requests
        gather_stub = MagicMock()
        gather_future = asyncio.Future()
        gather_future.set_result(None)
        gather_stub.return_value = gather_future
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather', gather_stub)

        # Set the job's number of clones to test
        number_of_clones = 10
        job.data['number_of_clones'] = number_of_clones

        # Prepare the job runner
        httpjobrunner.load_class(MagicMock(), MagicMock())
        runner = httpjobrunner()

        # Run the job with some fake data, but use job with prepared number of clones
        await runner.run(job, 0)

        # Assert that asyncio.gather was called with 10 calls to runner.handle_request
        gather_stub.assert_called_once_with(*[runner.handle_request(job)
                                              for _ in range(number_of_clones)])

        # The code which actually awaits the future is stubbed, so I have to cancel the future
        gather_future.cancel()
