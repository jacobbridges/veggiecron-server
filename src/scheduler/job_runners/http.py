"""
src/scheduler/job_runners/http.py

Job runner for handling all jobs with the "http" type.
"""

import asyncio
import json

from tornado.httpclient import AsyncHTTPClient
from tornado.platform.asyncio import to_asyncio_future

from ._base import AbstractJobRunner, Job
from ...database import DB
from ...utils.dates import now


class HTTPJobRunner(AbstractJobRunner):
    """Responsible for running HTTP jobs."""

    # Will be overwritten in load_class class method.
    http_client = None
    scheduler_queue = None

    # Maximum number of open requests at any given time
    # NOTE: if this number is too large, it will hold up the event loop.
    max_open_requests = 200

    @classmethod
    def load_class(cls, db: DB, scheduler_queue: asyncio.Queue):
        """Prepare any resources to be shared among all instances of this job runner."""
        # Create a tornado async HTTP client for making requests
        cls.http_client = AsyncHTTPClient(max_clients=cls.max_open_requests)

        # Bind the database connection to the class
        cls.db = db

        # Bind the scheduler queue to the class
        cls.scheduler_queue = scheduler_queue

    def load(self):
        """Prepare any resources for this instance of the job runner."""
        pass

    async def run(self, job: Job, delay: float):
        """Run an HTTP job."""
        # Delay the job execution until the scheduled time
        if delay > 0:
            await asyncio.sleep(delay)

        # "Queue up" x HTTP requests, where x is the job's "number_of_clones"
        num_clones = job.data['number_of_clones'] or 1
        job_future = asyncio.gather(*[self.handle_request(job) for _ in range(num_clones)])

        # If shadows are enabled, add the queued requests as a Task to the event loop
        if job.data['enable_shadows'] is True:
            asyncio.ensure_future(job_future)
        # Else if shadows are disabled, wait for the requests to finish before executing rest of
        # the function
        else:
            await job_future

        # Set the job's last run time to now and persist changes to the database
        job.last_ran = now(as_utc=True)
        await self.db.execute('UPDATE job SET last_ran = ? WHERE id = ?', job.last_ran, job.id)

        # If the job should repeat, schedule it
        if job.run_once is False:
            await self.scheduler_queue.put(job)
        # Else if the job should only run once, set the job to done and persist changes to datbase
        else:
            job.done = 1
            asyncio.ensure_future(self.db.execute('UPDATE job SET done = 1 WHERE id = ?',
                                                  job.id))

    async def handle_request(self, job):
        try:
            response = await to_asyncio_future(self.http_client.fetch(job.data['url'],
                                                                      method=job.data['verb']))
            result = json.dumps({'code': response.code, 'body': response.body.decode('utf8')})
            asyncio.ensure_future(self.persist_job_run(job, result))
        except Exception as e:
            asyncio.ensure_future(
                self.persist_job_run(job, json.dumps({'code': 0, 'body': str(e)}))
            )

    async def persist_job_run(self, job, result):
        """Persist the results of a job."""
        return await self.db.execute('INSERT INTO job_result (job_id, result, date_created) '
                                     'VALUES (?, ?, ?)', job.id, result, now(as_utc=True))
