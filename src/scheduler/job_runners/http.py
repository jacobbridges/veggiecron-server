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
        job_future = asyncio.gather(*[self.handle_request(job)
                                      for _ in range(job.data['number_of_clones'])])

        # Create an async function for running the job with shadows disabled
        async def run_with_shadows():
            asyncio.ensure_future(job_future)
            job.last_ran = now(as_utc=True)
            await self.db.execute('UPDATE job SET last_ran = ? WHERE id = ?', job.last_ran, job.id)
            if job.run_once is False:
                await self.scheduler_queue.put(job)
            else:
                asyncio.ensure_future(self.db.execute('UPDATE job SET done = 1 WHERE id = ?',
                                                      job.id))

        # Create an async function for running the job with shadows enabled
        async def run_without_shadows():
            await job_future
            job.last_ran = now(as_utc=True)
            await self.db.execute('UPDATE job SET last_ran = ? WHERE id = ?', job.last_ran, job.id)
            if job.run_once is False:
                await self.scheduler_queue.put(job)
            else:
                asyncio.ensure_future(self.db.execute('UPDATE job SET done = 1 WHERE id = ?',
                                                      job.id))

        # Run the job and depending on the "enable_shadows" option either queue the job right away
        # or after the job finishes running
        if job.data['enable_shadows'] is True:
            asyncio.ensure_future(run_with_shadows())
        else:
            asyncio.ensure_future(run_without_shadows())

    async def handle_request(self, job):
        response = await to_asyncio_future(self.http_client.fetch(job.data['url'],
                                                                  method=job.data['verb']))
        result = json.dumps({'code': response.code, 'body': response.body.decode('utf8')})
        asyncio.ensure_future(self.persist_job_run(job, result))

    async def persist_job_run(self, job, result):
        """Persist the results of a job."""
        return await self.db.execute('INSERT INTO job_result (job_id, result, date_created) '
                                     'VALUES (?, ?, ?)', job.id, result, now(as_utc=True))
