import pprint
import time
import json

from gtmcore.dispatcher import Dispatcher, jobs
from lmsrvlabbook.tests.fixtures import fixture_working_dir


class TestLabBookServiceQueries(object):

    def test_query_finished_task(self, fixture_working_dir):
        """Test listing labbooks"""
        d = Dispatcher()
        job_id = d.dispatch_task(jobs.test_exit_success)
        time.sleep(1)

        query = """
        {
            jobStatus(jobId: "%s") {
                result
                status
                jobMetadata
                failureMessage
                startedAt
                finishedAt
            }
        }
        """ % job_id.key_str
        r = fixture_working_dir[2].execute(query)
        assert 'errors' not in r
        assert int(r['data']['jobStatus']['result']) == 0
        assert r['data']['jobStatus']['status'] == 'finished'
        assert r['data']['jobStatus']['startedAt'] is not None
        assert r['data']['jobStatus']['failureMessage'] is None
        assert r['data']['jobStatus']['finishedAt']
        assert r['data']['jobStatus']['jobMetadata'] == '{}'

    def test_query_failed_task(self, fixture_working_dir):
        """Test listing labbooks"""

        d = Dispatcher()
        job_id = d.dispatch_task(jobs.test_exit_fail)
        time.sleep(1)

        query = """
        {
            jobStatus(jobId: "%s") {
                result
                status
                jobMetadata
                failureMessage
                startedAt
                finishedAt
            }
        }
        """ % job_id

        r = fixture_working_dir[2].execute(query)
        assert 'errors' not in r
        assert r['data']['jobStatus']['result'] is None
        assert r['data']['jobStatus']['status'] == 'failed'
        assert r['data']['jobStatus']['failureMessage'] == \
               'Exception: Intentional Exception from job `test_exit_fail`'
        assert r['data']['jobStatus']['startedAt'] is not None
        assert r['data']['jobStatus']['finishedAt'] is not None
        # Assert the following dict is empty
        assert not json.loads(r['data']['jobStatus']['jobMetadata'])

    def test_query_started_task(self, fixture_working_dir):
        """Test listing labbooks"""

        d = Dispatcher()

        job_id = d.dispatch_task(jobs.test_sleep, args=(2,))

        time.sleep(1)

        query = """
        {
            jobStatus(jobId: "%s") {
                result
                status
                jobMetadata
                failureMessage
                startedAt
                finishedAt
            }
        }
        """ % job_id

        try:
            r = fixture_working_dir[2].execute(query)
            pprint.pprint(r)
            assert 'errors' not in r
            assert r['data']['jobStatus']['result'] is None
            assert r['data']['jobStatus']['status'] == 'started'
            assert r['data']['jobStatus']['failureMessage'] is None
            assert r['data']['jobStatus']['startedAt'] is not None
            assert json.loads(r['data']['jobStatus']['jobMetadata'])['sample'] == 'test_sleep metadata'
        finally:
            # Make sure all the jobs finish.
            time.sleep(3)
