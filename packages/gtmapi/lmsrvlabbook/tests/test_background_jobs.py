# Copyright (c) 2017 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import time

from lmsrvlabbook.tests.fixtures import fixture_working_dir_env_repo_scoped
from gtmcore.dispatcher import Dispatcher, jobs


class TestBackgroundJobs(object):
    def test_get_background_jobs_basics(self, fixture_working_dir_env_repo_scoped):

        d = Dispatcher()
        time.sleep(0.25)
        t1 = d.dispatch_task(jobs.test_exit_fail).key_str
        t2 = d.dispatch_task(jobs.test_exit_success).key_str
        t3 = d.dispatch_task(jobs.test_sleep, args=(5,)).key_str

        query = """
                {
                  backgroundJobs {
                    edges {
                      node {
                        id
                        jobKey
                        failureMessage
                        status
                        result
                      }
                    }
                  }
                }
        """
        time.sleep(1)
        try:
            time1 = time.time()
            result = fixture_working_dir_env_repo_scoped[2].execute(query)
            time2 = time.time()
            tdiff = time2 - time1
            assert tdiff < 0.5, "Query should not take more than a few millis (took {}s)".format(tdiff)

            assert any([t1 == x['node']['jobKey']
                        and 'failed' == x['node']['status']
                        and 'Exception: ' in x['node']['failureMessage']
                        for x in result['data']['backgroundJobs']['edges']])
            assert any([t2 == x['node']['jobKey'] and "finished" == x['node']['status']
                        and x['node']['failureMessage'] is None
                        for x in result['data']['backgroundJobs']['edges']])
            assert any([t3 == x['node']['jobKey'] and "started" == x['node']['status']
                        and x['node']['failureMessage'] is None
                        for x in result['data']['backgroundJobs']['edges']])
        finally:
            time.sleep(2)
