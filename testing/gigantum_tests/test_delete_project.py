import logging
import time
import os

import docker
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import testutils


def test_delete_project(driver: selenium.webdriver, *args, **kwargs):
    """
        Test that deleting a project in Gigantum deletes it from the file system.

        Args:
            driver
    """
    r = testutils.prep_py3_minimal_base(driver)
    username, project_name = r.username, r.project_name

    # Check that project path exists on file system
    logging.info("Checking that the project exists in the file system")
    project_path = os.path.join(os.environ['GIGANTUM_HOME'], username,
                                username, 'labbooks', project_name)
    assert os.path.exists(project_path), \
        f"Project {project_name} should exist at {project_path}"
    logging.info("Finding project Docker image")
    dc = docker.from_env()
    project_img = []
    for img in dc.images.list():
        for t in img.tags:
            if 'gmlb-' in t and project_name in t:
                logging.info(f"Found Docker image {t} for {project_name}")
                project_img.append(img)
    assert len(project_img) == 1, f"Must be one docker tag for {project_name}"

    # Navigate to the "Delete Project" button and click it
    logging.info("Navigating to 'Delete Project' and delete the project")
    driver.find_element_by_css_selector(".ActionsMenu__btn").click()
    time.sleep(3)
    driver.find_element_by_css_selector(".ActionsMenu__item--delete").click()
    time.sleep(3)
    driver.find_element_by_css_selector("#deleteInput").send_keys(project_name.lstrip())
    driver.find_element_by_css_selector(".DeleteLabbook .ButtonLoader").click()
    time.sleep(5)

    # Check all post conditions for delete:
    # 1. Does not exist in filesystem, and
    # 2. Docker image no longer exists
    logging.info("Checking that project path and project Docker image no longer exist")
    assert not os.path.exists(project_path), f"Project at {project_path} not deleted"
    project_img = []
    for img in dc.images.list():
        for t in img.tags:
            if 'gmlb-' in t and project_name in t:
                logging.error(f'Docker tag {t} still exists for deleted project {project_name}')
                project_img.append(img)
    assert len(project_img) == 0, \
        f"Docker image for {project_path}: {project_img[0]} still exists"
