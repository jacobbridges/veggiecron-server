"""
src/scheduler/job_scheduler.py

Code related to running jobs, scheduling jobs, etc.
"""

import asyncio

from asyncio import Queue
from threading import Thread
from tornado.httpclient import AsyncHTTPClient
from tornado.platform.asyncio import to_asyncio_future

from .job import Job
from .job_runners import AbstractJobRunner, HTTPJobRunner
from ..database import DB
from ..utils.dates import now
from .parser import parse


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

        # Prepare all job runners
        HTTPJobRunner.load_class(db, work_queue)

        # Call the parent (Thread) constructor
        super().__init__()

    def run(self):
        """Main function of this thread."""

        self.setName('Thread-JobScheduler')

        # Create the event loop
        asyncio.set_event_loop(self.event_loop)

        async def main():

            # Create an asynchronous http client
            # TODO: Possible method of speeding up the http client?
            http_client = AsyncHTTPClient(max_clients=50)

            # First time this thread is run, find all jobs which are not complete and reschedule
            # them.
            query_result = await self.db.execute("SELECT * FROM job WHERE done = 0;")
            for row in query_result:
                await self.work_queue.put(Job(*row))

            # Create a mapping of job types to job runners
            job_runners = {
                1: HTTPJobRunner(),
            }

            # Process jobs from the work queue
            while True:
                job = await self.work_queue.get()
                ":type: Job"

                # If "False" is sent to the work queue, end the thread
                if job is False:
                    break

                # If the job doesn't have a last_ran time, use the date_created time
                if job.last_ran is None:
                    job.last_ran = float(job.date_created)

                # Calculate the job's next run time
                next_run = parse(job.schedule, job.last_ran)

                # Get the appropriate job runner
                job_runner = job_runners.get(job.type_id)
                ":type: AbstractJobRunner"

                # Schedule the job to run
                if next_run <= now():
                    self << 'Job "{}" is behind schedule! Running now!'.format(job.name)
                    asyncio.ensure_future(job_runner.run(job, 0))
                else:
                    seconds = next_run.timestamp() - now().timestamp()
                    self << 'Scheduling job "{}" to run in {:.2f} seconds'.format(job.name, seconds)
                    asyncio.ensure_future(job_runner.run(job, seconds))

                # Job has been scheduled, move on to scheduling the next job
                self.work_queue.task_done()

        asyncio.ensure_future(to_asyncio_future(main()))

    def __lshift__(self, msg):
        """Helper function for printing a message."""
        msg = '[JobScheduler] ' + msg
        print(msg)
