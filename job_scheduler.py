"""
/job_scheduler.py

Code related to running jobs, scheduling jobs, etc.
"""

import asyncio
import json

from asyncio import Queue
from threading import Thread
from tornado.httpclient import AsyncHTTPClient
from tornado.platform.asyncio import to_asyncio_future

from util import now, now_as_utc
from database import DB
from schedule_parser import parse


class JobScheduler(Thread):
    """A separate thread from the main process which runs and schedules jobs."""

    def __init__(self, work_queue: Queue, db: DB, event_loop):
        """Constructor."""

        # Bind the work_queue to the thread
        self.work_queue = work_queue

        # Bind the database connection to the thread
        self.db = db

        # Bind the event loop to the thread
        self.event_loop = event_loop

        # Call the parent (Thread) constructor
        super().__init__()

    def run(self):
        """Main function of this thread."""

        self.setName('Thread-JobScheduler')

        # Create the event loop
        asyncio.set_event_loop(self.event_loop)

        async def handle_request(client, url, verb, job_id):
            try:
                response = await to_asyncio_future(client.fetch(url, method=verb))
                # TODO: Save the response somewhere (for future retrieval)
                data = {'code': response.code, 'body': response.body.decode('utf8')}
                future = self.db.execute('INSERT INTO job_result (job_id, result, date_created) '
                                         'VALUES (?, ?, ?)', job_id, json.dumps(data), now_as_utc())
                asyncio.ensure_future(future)
            except Exception as e:
                self << 'Failed to {} {} (ERROR: "{}")'.format(verb, url, str(e))

        async def run_job(job, delay, http_client):
            if delay > 0:
                await asyncio.sleep(delay)
            url, concurrency, verb = job.data['url'], job.data['number_of_clones'], job.data['verb']
            await self.db.execute('UPDATE job SET last_ran = ? WHERE id = ?',
                                  job.last_ran, job.id)
            job_future = asyncio.gather(*[handle_request(http_client, u, verb, job.id)
                                          for u in [url] * concurrency])
            if job.data['enable_shadows'] is True:
                asyncio.ensure_future(job_future)
                await self.work_queue.put(job)
            else:
                async def f():
                    await job_future
                    await self.work_queue.put(job)
                asyncio.ensure_future(f())

        async def main():

            # Create an asynchronous http client
            # TODO: Possible method of speeding up the http client?
            http_client = AsyncHTTPClient(max_clients=50)

            # First time this thread is run, find all jobs which are not complete and reschedule
            # them.
            query_result = await self.db.execute("SELECT * FROM job WHERE done = 0;")
            for row in query_result:
                await self.work_queue.put(Job(*row))

            # Process jobs from the work queue
            while True:
                ":type: Job"
                job = await self.work_queue.get()

                # If "False" is sent to the work queue, end the thread
                if job is False:
                    break

                # Process the job
                if job.last_ran is None:
                    job.last_ran = now().timestamp()
                else:
                    job.last_ran = float(job.last_ran)
                next_run = parse(job.schedule, job.last_ran)

                if next_run <= now():
                    self << 'Job "{}" is behind schedule! Running now!'.format(job.name)
                    job.last_ran = now().timestamp()
                    asyncio.ensure_future(run_job(job, 0, http_client))
                else:
                    seconds = next_run.timestamp() - now().timestamp()
                    self << 'Scheduling job "{}" to run in {} seconds'.format(job.name, seconds)
                    job.last_ran = next_run.timestamp()
                    asyncio.ensure_future(run_job(job, seconds, http_client))
                self.work_queue.task_done()

        asyncio.ensure_future(to_asyncio_future(main()))

    async def schedule_job(self, job):
        """Schedule a job to be processed."""
        return await self.work_queue.put(job)

    def __lshift__(self, msg):
        """Helper function for printing a message."""
        msg = '[JobScheduler] ' + msg
        print(msg)


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
        self.last_ran = last_ran
        self.date_created = date_created
        self.date_updated = date_updated
