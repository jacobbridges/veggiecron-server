"""
tests/test_http_job_runner.py

Test the the job runner which handles all http jobs.
"""
import asyncio
import pytest

from unittest.mock import MagicMock, call


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
    async def test_delay_on_run(self, monkeypatch, httpjobrunner, job, event_loop):
        """Should delay the execution of run() if delay parameter is greater than zero."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            asyncio.coroutine(MagicMock()))
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub the sleep coroutine
        sleep_stub = MagicMock()
        sleep_coro = asyncio.coroutine(sleep_stub)
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.sleep', sleep_coro)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(MagicMock())
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data, but be sure the delay is above 0
        delay = 1
        await runner.run(job, delay)

        # Assert that asyncio.sleep was called with the delay
        sleep_stub.assert_called_once_with(delay)

    @pytest.mark.asyncio
    async def test_make_requests_for_num_of_clones_on_run(self, monkeypatch, httpjobrunner, job):
        """Should "queue up" x HTTP requests on run(), where x is the job's "number_of_clones"."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            asyncio.coroutine(MagicMock()))

        # Stub the method which handles http requests
        handle_request_stub = MagicMock()
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            handle_request_stub)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(MagicMock())
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        number_of_clones = 4
        job.data['number_of_clones'] = number_of_clones
        await runner.run(job, 0)

        # Assert that asyncio.gather was called with
        assert handle_request_stub.call_count is number_of_clones

    @pytest.mark.asyncio
    async def test_make_at_least_one_request_on_run(self, monkeypatch, httpjobrunner, job):
        """Should "queue up" at least one HTTP request on run()"""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            asyncio.coroutine(MagicMock()))

        # Stub the method which handles http requests
        handle_request_stub = MagicMock()
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            handle_request_stub)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(MagicMock())
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        job.data['number_of_clones'] = 0
        await runner.run(job, 0)

        # Assert the job.handle_request method was called at least once
        assert handle_request_stub.call_count is 1

    @pytest.mark.asyncio
    async def test_shadow_enabled_on_run(self, monkeypatch, httpjobrunner, job):
        """Should ensure HTTP requests when shadows are enabled on run()"""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub ensure_future function, so I can check later that the requests were ensured
        gather_response = 'fake data!'
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            MagicMock(return_value=gather_response))
        ensure_future_stub = MagicMock()
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future',
                            ensure_future_stub)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(MagicMock())
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        job.data['enable_shadows'] = True
        await runner.run(job, 0)

        # Assert that the http requests were ensured
        assert call(gather_response) in ensure_future_stub.call_args_list

    @pytest.mark.asyncio
    async def test_shadow_disabled_on_run(self, monkeypatch, httpjobrunner, job):
        """Should await HTTP requests when shadows are disabled on run()"""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())

        # Stub asyncio.gather function, so I can check later that the requests were awaited
        gather_stub = MagicMock()
        gather_coro = asyncio.coroutine(gather_stub)
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather', gather_coro)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(MagicMock())
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        job.data['enable_shadows'] = False
        await runner.run(job, 0)

        # Assert that the http requests were awaited
        gather_stub.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_last_ran_field_updated_on_run(self, monkeypatch, httpjobrunner, job):
        """Should update job's "last_ran" field on run()."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            asyncio.coroutine(MagicMock()))
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub the now function so I can test that it was called
        now_time = 'time right now'
        now_stub = MagicMock(return_value=now_time)
        monkeypatch.setattr('src.scheduler.job_runners.http.now', now_stub)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        execute_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(execute_stub)
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        await runner.run(job, 0)

        # Assert the job's last_ran field is set the the response from now()
        assert now_time is job.last_ran
        # Assert the job's updated "last_ran" field is persisted to the database
        assert (call('UPDATE job SET last_ran = ? WHERE id = ?', job.last_ran, job.id)
                in execute_stub.call_args_list)

    @pytest.mark.asyncio
    async def test_job_is_rescheduled_on_run(self, monkeypatch, httpjobrunner, job):
        """Should reschedule the job if run_once field is False on run()."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            asyncio.coroutine(MagicMock()))
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        db_stub.execute = asyncio.coroutine(MagicMock())
        scheduler_queue_stub = MagicMock()
        put_stub = MagicMock()
        put_coro = asyncio.coroutine(put_stub)
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        job.run_once = False
        await runner.run(job, 0)

        # Assert the job was sent to the queue for rescheduling
        put_stub.assert_called_once_with(job)

    @pytest.mark.asyncio
    async def test_job_is_set_to_done_on_run(self, monkeypatch, httpjobrunner, job):
        """Should set the job to done if run_once field is True and persist on run()."""
        # Stub all external and internal methods that are not being tested
        monkeypatch.setattr('src.scheduler.job_runners.http.AsyncHTTPClient', MagicMock())
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.gather',
                            asyncio.coroutine(MagicMock()))
        monkeypatch.setattr('src.scheduler.job_runners.http.HTTPJobRunner.handle_request',
                            MagicMock())

        # Stub "ensure_future" so I can test that it was called for the database persistence
        ensure_future_stub = MagicMock()
        monkeypatch.setattr('src.scheduler.job_runners.http.asyncio.ensure_future',
                            ensure_future_stub)

        # Stub the database and scheduler_queue as mocks inside coroutines
        db_stub = MagicMock()
        execute_stub = MagicMock()
        execute_coro = asyncio.coroutine(execute_stub)
        db_stub.execute = execute_coro
        scheduler_queue_stub = MagicMock()
        put_coro = asyncio.coroutine(MagicMock())
        scheduler_queue_stub.put = put_coro

        # Prepare the job runner class
        httpjobrunner.load_class(db_stub, scheduler_queue_stub)
        runner = httpjobrunner()

        # Run the job with some fake data
        job.run_once = True
        await runner.run(job, 0)

        # Assert the job's "done" field has been set to 1
        assert job.done is 1
        # Assert the job's updated "done" field was ensured to be persisted to the database
        # NOTE: I could not assert "ensure_future" was called with the stubbed execute coroutine,
        # because a new coroutine is created on every execution and db.execute is called multiple
        # times in run(). There are no async MagicMocks, so for now this is the best I can do.
        assert ensure_future_stub.call_count is 1
