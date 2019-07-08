import time
import os
import logging

import testutils
from testutils import TestTags
from testutils.graphql_helpers import create_py3_minimal_project, list_local_projects


@TestTags('graphql')
def test_time_list_local_projects(driver, *args, **kwargs):
    # Project set up
    username = testutils.log_in(driver)

    time.sleep(1)
    testutils.GuideElements(driver).remove_guide()
    # Let everything sort and get cached.
    time.sleep(6)
    driver.get(f'{os.environ["GIGANTUM_HOST"]}/api/version')


    t0 = time.time()
    results = list_local_projects()
    tList = time.time() - t0
    #print(results)

    logging.warning(f"Listed {len(results)} projects in {tList:.2f}sec")

