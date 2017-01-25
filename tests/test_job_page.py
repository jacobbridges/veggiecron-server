"""
tests/test_job_page.py

Test the job page ("/job"). A get request will list all jobs for the current user, and a post
request will create a new cron job in the database.
"""

import json
import pytest
import tornado.gen
import tornado.testing
import tornado.httpclient

from unittest.mock import patch
from tornado.web import HTTPError
from urllib.parse import urlencode

from tests._base_test_cases import MyServerTestCase
from tests import fixtures


class TestGetJobPage(MyServerTestCase):
    """GET '/job'"""

    def test_error_response_code_with_no_auth_token(self):
        """Should have a response code of 401 if no auth token is provided."""
        self.stub_validate_auth_token(HTTPError(status_code=401))
        response = self.fetch('/job')
        self.assertEqual(response.code, 401)

    def test_error_response_code_with_invalid_auth_token(self):
        """Should have a response code of 401 if an invalid auth token is provided."""
        self.stub_validate_auth_token(HTTPError(status_code=401))
        response = self.fetch('/job', headers={'X-Auth-Token': 'invalidToken'})
        self.assertEqual(response.code, 401)

    def test_success_response_code_with_good_token(self):
        """Should have a response code of 200 if a valid auth token is provided."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_jobs_with_type)
        response = self.fetch('/job', headers={'X-Auth-Token': 'validToken'})
        self.assertEqual(response.code, 200)

    def test_response_is_json(self):
        """Should have a JSON encoded body."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_jobs_with_type)
        response = self.fetch('/job', headers={'X-Auth-Token': 'validToken'})
        try:
            json.loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    def test_response_has_keys(self):
        """Should have keys "id", "data", and "description" in response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_jobs_with_type)
        response = self.fetch('/job', headers={'X-Auth-Token': 'validToken'})
        res_json = json.loads(response.body)
        self.assertIn('id', res_json, 'Key "id" not found in response.')
        self.assertIn('data', res_json, 'Key "data" not found in response.')
        self.assertIn('description', res_json, 'Key "description" not found in response.')

    def test_response_has_jobs(self):
        """Should have a list of jobs in the response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_jobs_with_type)
        response = self.fetch('/job', headers={'X-Auth-Token': 'validToken'})
        res_json = json.loads(response.body)
        self.assertIn('data', res_json, 'Key "data" not found in response.')
        self.assertIn('jobs', res_json['data'], 'Key "jobs" not found in response.data.')
        self.assertTrue(type(res_json['data']['jobs']) is list,
                        'response.data.jobs should be a list.')
        for job in res_json['data']['jobs']:
            self.assertIn('data', job, 'Key "data" not found in job.')
            self.assertTrue(type(job['data']) is str, 'job.data should be a string.')
            self.assertIn('done', job, 'Key "done" not found in job.')
            self.assertTrue(type(job['done']) is bool, 'job.done should be a boolean.')
            self.assertIn('last_ran', job, 'Key "last_ran" not found in job.')
            self.assertTrue(type(job['last_ran']) is str, 'job.last_ran should be a string.')
            self.assertIn('name', job, 'Key "name" not found in job.')
            self.assertTrue(type(job['name']) is str, 'job.name should be a string.')
            self.assertIn('schedule', job, 'Key "schedule" not found in job.')
            self.assertTrue(type(job['schedule']) is str, 'job.schedule should be a string.')
            self.assertIn('type', job, 'Key "type" not found in job.')
            self.assertTrue(type(job['type']) is str, 'job.type should be a string.')


@patch('src.utils.dates.utc_to_date', fixtures.create_fixture_func)
class TestGetJobResultPage(MyServerTestCase):
    """GET '/job?name=<job_name>'"""

    def test_error_response_code_when_job_dne(self):
        """Should have a response code of 404 if job_name does not exist."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([])
        response = self.fetch('/job?name=does_not_exist', headers={'X-Auth-Token': 'validToken'})
        self.assertEqual(response.code, 404)

    def test_success_response_code_when_job_exists(self):
        """Should have a response code of 200 if a job_name exists."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([fixtures.db_response_jobs_with_type[0]],
                             fixtures.db_response_job_results)
        response = self.fetch('/job?name=exists', headers={'X-Auth-Token': 'validToken'})
        self.assertEqual(response.code, 200)

    def test_response_is_json(self):
        """Should have a response code of 200 if a job_name exists."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([fixtures.db_response_jobs_with_type[0]],
                             fixtures.db_response_job_results)
        response = self.fetch('/job?name=exists', headers={'X-Auth-Token': 'validToken'})
        try:
            json.loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    def test_response_has_keys(self):
        """Should have keys "id", "data", and "description" in response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([fixtures.db_response_jobs_with_type[0]],
                             fixtures.db_response_job_results)
        response = self.fetch('/job?name=exists', headers={'X-Auth-Token': 'validToken'})
        res_json = json.loads(response.body)
        self.assertIn('id', res_json, 'Key "id" not found in response.')
        self.assertIn('data', res_json, 'Key "data" not found in response.')
        self.assertIn('description', res_json, 'Key "description" not found in response.')

    def test_response_has_job_info(self):
        """Should have information about the job in the response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([fixtures.db_response_jobs_with_type[0]],
                             fixtures.db_response_job_results)
        response = self.fetch('/job?name=exists', headers={'X-Auth-Token': 'validToken'})
        res_json = json.loads(response.body)
        self.assertIn('job', res_json['data'], 'Key "job" not found in response.data.')
        job = res_json['data']['job']
        self.assertIn('data', job, 'Key "data" not found in response.data.job.')
        self.assertTrue(type(job['data']) is str, 'job.data should be a string.')
        self.assertIn('done', job, 'Key "done" not found in response.data.job.')
        self.assertTrue(type(job['done']) is bool, 'job.done should be a string.')
        self.assertIn('last_ran', job, 'Key "last_ran" not found in response.data.job.')
        self.assertTrue(type(job['last_ran']) is str, 'job.last_ran should be a string.')
        self.assertIn('name', job, 'Key "name" not found in response.data.job.')
        self.assertTrue(type(job['name']) is str, 'job.name should be a string.')
        self.assertIn('schedule', job, 'Key "schedule" not found in response.data.job.')
        self.assertTrue(type(job['schedule']) is str, 'job.schedule should be a string.')
        self.assertIn('type', job, 'Key "type" not found in response.data.job.')
        self.assertTrue(type(job['type']) is str, 'job.type should be a string.')

    def test_response_has_job_runs(self):
        """Should have a list of job runs in the response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([fixtures.db_response_jobs_with_type[0]],
                             fixtures.db_response_job_results)
        response = self.fetch('/job?name=exists', headers={'X-Auth-Token': 'validToken'})
        res_json = json.loads(response.body)
        self.assertIn('job_runs', res_json['data'], 'Key "job" not found in response.data.')
        for i, job_run in enumerate(res_json['data']['job_runs']):
            self.assertIn('result', job_run, 'Key "result" not found in job_runs[%i].' % i)
            self.assertTrue(type(job_run['result']) is str, 'job_run.result should be a string.')
            self.assertIn('timestamp', job_run, 'Key "result" not found in job_runs[%i].' % i)
            self.assertTrue(type(job_run['timestamp']) is str,
                            'job_run.timestamp should be a string.')


@patch('src.scheduler.Job', fixtures.create_fixture_func(None))
class TestPostJobPage(MyServerTestCase):
    """POST '/job'"""

    @tornado.testing.gen_test
    def test_error_response_code_with_no_auth_token(self):
        """Should have a response code of 401 if no auth token is provided."""
        valid_auth_token_stub = self.stub_validate_auth_token(HTTPError(status_code=401))
        future = self.http_client.fetch(self.get_url('/job'), method='POST', body='')
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 401)
        valid_auth_token_stub.assert_called_once_with(None)

    @tornado.testing.gen_test
    def test_error_response_code_with_invalid_auth_token(self):
        """Should have a response code of 401 if an invalid auth token is provided."""
        invalid_token = 'invalidToken'
        valid_auth_token_stub = self.stub_validate_auth_token(HTTPError(status_code=401))
        future = self.http_client.fetch(self.get_url('/job'), method='POST', body='',
                                        headers={'X-Auth-Token': invalid_token})
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 401)
        valid_auth_token_stub.assert_called_once_with(invalid_token)

    @tornado.testing.gen_test
    def test_error_response_code_no_arg(self):
        """Should have a response code of 400 if no args are provided."""
        self.stub_validate_auth_token(1)
        future = self.http_client.fetch(self.get_url('/job'), method='POST', body='',
                                        headers={'X-Auth-Token': 'token'})
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_error_response_code_missing_arg(self):
        """Should have a response code of 400 if any required args are missing."""

        # This stub will be called once for every param in fixtures.request_create_job_params
        self.stub_validate_auth_token(*([1] * len(fixtures.request_create_job_params)))

        # Run the request for every arg, leaving one out every time and testing for error
        def prepared_request(b):
            return self.http_client.fetch(self.get_url('/job'), method='POST', body=b,
                                          headers={'X-Auth-Token': 'token'})

        def dict_to_qs(d, ignore_keys=list()):
            return urlencode({k: v for k, v in d.items() if k not in ignore_keys})

        for arg in fixtures.request_create_job_params:
            future = prepared_request(dict_to_qs(fixtures.request_create_job_params,
                                                 ignore_keys=[arg]))
            with pytest.raises(tornado.httpclient.HTTPError) as error_info:
                yield future
            self.assertEqual(error_info.value.code, 400, 'Expected server to return an error '
                                                         'because request was missing argument '
                                                         '"{}"'.format(arg))

    @tornado.testing.gen_test
    def test_error_response_code_job_type_dne(self):
        """Should have a response code of 400 if the job type does not exist."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute([])
        local_params = fixtures.request_create_job_params.copy()
        local_params['type'] = 'does_not_exist'
        future = self.http_client.fetch(self.get_url('/job'), method='POST',
                                        body=urlencode(local_params),
                                        headers={'X-Auth-Token': 'token'})
        with pytest.raises(tornado.httpclient.HTTPError) as error_info:
            yield future
        self.assertEqual(error_info.value.code, 400)

    @tornado.testing.gen_test
    def test_success_response_code_good_request(self):
        """Should have a response code of 200 if the request has all the right information."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_job_type, None, fixtures.db_response_job)
        self.stub_scheduler_queue_put(None)
        response = yield self.http_client.fetch(self.get_url('/job'), method='POST',
                                                body=urlencode(fixtures.request_create_job_params),
                                                headers={'X-Auth-Token': 'token'})
        self.assertEqual(response.code, 200)

    @tornado.testing.gen_test
    def test_response_is_json(self):
        """Should have a JSON encoded body."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_job_type, None, fixtures.db_response_job)
        self.stub_scheduler_queue_put(None)
        response = yield self.http_client.fetch(self.get_url('/job'), method='POST',
                                                body=urlencode(fixtures.request_create_job_params),
                                                headers={'X-Auth-Token': 'token'})
        try:
            json.loads(response.body)
        except ValueError:
            pytest.fail('Response body was not JSON encoded.')

    @tornado.testing.gen_test
    def test_response_has_keys(self):
        """Should have keys "id", "data", and "description" in response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_job_type, None, fixtures.db_response_job)
        self.stub_scheduler_queue_put(None)
        response = yield self.http_client.fetch(self.get_url('/job'), method='POST',
                                                body=urlencode(fixtures.request_create_job_params),
                                                headers={'X-Auth-Token': 'token'})
        res_json = json.loads(response.body)
        self.assertIn('id', res_json, 'Key "id" not found in response.')
        self.assertIn('data', res_json, 'Key "data" not found in response.')
        self.assertIn('description', res_json, 'Key "description" not found in response.')

    @tornado.testing.gen_test
    def test_response_has_job_info(self):
        """Should have information about the new job in the response."""
        self.stub_validate_auth_token(1)
        self.stub_db_execute(fixtures.db_response_job_type, None, fixtures.db_response_job)
        self.stub_scheduler_queue_put(None)
        response = yield self.http_client.fetch(self.get_url('/job'), method='POST',
                                                body=urlencode(fixtures.request_create_job_params),
                                                headers={'X-Auth-Token': 'token'})
        res_json = json.loads(response.body)
        job = res_json['data']
        self.assertIn('data', job, 'Key "data" not found in response.data.')
        self.assertTrue(type(job['data']) is str, 'job.data should be a string.')
        self.assertIn('date_created', job, 'Key "date_created" not found in response.data.')
        self.assertTrue(type(job['date_created']) is float, 'job.date_created should be a float.')
        self.assertIn('name', job, 'Key "name" not found in response.data.')
        self.assertTrue(type(job['name']) is str, 'job.name should be a string.')
        self.assertIn('schedule', job, 'Key "schedule" not found in response.data.')
        self.assertTrue(type(job['schedule']) is str, 'job.schedule should be a string.')
        self.assertIn('type', job, 'Key "type" not found in response.data.')
        self.assertTrue(type(job['type']) is str, 'job.type should be a string.')