"""
src/routes/job.py

Job "/job" route for all HTTP methods.
"""

from tornado.web import HTTPError

from ._base import BasePageHandler
from ..scheduler import Job
from ..utils.dates import utc_to_date, now


class JobPageHandler(BasePageHandler):

    async def get(self):
        # Check for auth token
        auth_token = self.request.headers.get('X-Auth-Token', None)
        user_id = await self.application.validate_auth_token(auth_token)

        job_name = self.get_query_argument('name', None)
        if job_name is None:

            # Get all jobs for user
            jobs = await self.db.execute("SELECT j.*, jt.name FROM job j "
                                         "JOIN job_type jt ON j.type_id = jt.id "
                                         "WHERE user_id = ?;", user_id)
            return self.write({
                'id': 'success',
                'description': 'List all jobs for the given user.',
                'data': {
                    'jobs': [
                        {
                            'name': j[2],
                            'type': j[10],
                            'data': j[4],
                            'schedule': j[5],
                            'last_ran': j[7],
                            'done': True if j[6] is 1 else False
                        } for j in jobs
                    ],
                }
            })

        else:

            # Get the job by name
            job = await self.db.execute("SELECT j.*, jt.name as type FROM job j "
                                        "JOIN job_type jt ON j.type_id = jt.id "
                                        "WHERE j.user_id = ? AND j.name = ?",
                                        user_id, job_name)
            if len(job) == 0:
                raise HTTPError(404, 'Job "{}" does not exist for the current user.'
                                .format(job_name))

            job = job[0]
            job_results = await self.db.execute("SELECT id, result, date_created FROM job_result "
                                                "WHERE job_id = ? ORDER BY id DESC LIMIT 25",
                                                job[0])

            return self.write({
                'id': 'success',
                'description': 'Information for job "{}"'.format(job_name),
                'data': {
                    'job': {
                        'name': job_name,
                        'type': job[10],
                        'data': job[4],
                        'schedule': job[5],
                        'last_ran': job[7],
                        'done': True if job[6] is 1 else False
                    },
                    'job_runs': [{'result': r[1], 'timestamp': utc_to_date(float(r[2])).isoformat()}
                                 for r in job_results]
                }
            })

    async def post(self):
        # Check for auth token
        auth_token = self.request.headers.get('X-Auth-Token', None)
        user_id = await self.application.validate_auth_token(auth_token)

        # Check all post arguments are supplied
        job_name = self.get_argument('name', None)
        job_type = self.get_argument('type', None)
        job_data = self.get_argument('data', None)
        job_schedule = self.get_argument('schedule', None)
        if any([job_name is None, job_type is None, job_data is None, job_schedule is None]):
            raise HTTPError(400, 'Must include the following form data: "name", "type", "data", '
                                 '"schedule"')

        # Create a job from the post data
        job_type_id = await self.db.execute("SELECT * FROM job_type WHERE name = ?", job_type)
        if job_type_id:
            job_type_id = job_type_id[0][0]
            time_now = now().timestamp()
            await self.db.execute('INSERT INTO job (id, user_id, name, type_id, data, schedule, '
                                  'date_created, date_updated) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);',
                                  user_id, job_name, job_type_id, job_data, job_schedule,
                                  time_now, time_now)
            job = await self.db.execute('SELECT * FROM job WHERE user_id = ? AND name = ?',
                                        user_id, job_name)
            job = job[0]
            job_obj = Job(*job)
            await self.scheduler.work_queue.put(job_obj)
            return self.write({
                'id': 'success',
                'description': 'Successfully created {0} job: "{1}"'.format(job_type, job_name),
                'data': {
                    'name': job_name,
                    'type': job_type,
                    'data': job_data,
                    'schedule': job_schedule,
                    'date_created': time_now,
                    'date_updated': time_now,
                }
            })
        else:
            raise HTTPError(400, 'Job type "{}" does not exist.'.format(job_type))
