import time
import os

import testutils
from testutils import TestTags
from testutils.graphql import create_py3_minimal_project


@TestTags('graphql')
def test_init_graphql(driver, *args, **kwargs):
    # Project set up
    username = testutils.log_in(driver)
    time.sleep(1)
    testutils.GuideElements(driver).remove_guide()
    time.sleep(1)
    owner, proj_name = create_py3_minimal_project(testutils.unique_project_name())
    time.sleep(1)
    driver.get(f'{os.environ["GIGANTUM_HOST"]}/projects/{username}/{proj_name}')

    time.sleep(5)
