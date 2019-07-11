import logging
import time

import selenium
from selenium.webdriver.common.by import By

import testutils


def test_project_file_browser(driver: selenium.webdriver, *args, **kwargs):
    """
    Test that a file can be dragged and dropped into code, input data,
    and output data in a project.

    Args:
        driver
    """
    r = testutils.prep_py3_minimal_base(driver)
    username, project_title = r.username, r.project_name
    logging.info(f"Navigating to Code for project: {project_title}")
    file_browser_elts = testutils.FileBrowserElements(driver)
    file_browser_elts.code_tab.wait().click()
    time.sleep(2)
    logging.info(f"Dragging and dropping file into code for project: {project_title}")
    file_browser_elts.drag_drop_file_in_drop_zone()

    assert file_browser_elts.file_information.find().text == 'sample-upload.txt', \
        "Expected sample-upload.txt to be the first file in Code"

    logging.info(f"Navigating to Input Data for project: {project_title}")
    file_browser_elts.input_data_tab.wait().click()
    time.sleep(2)
    logging.info(f"Dragging and dropping file into Input Data for project: {project_title}")
    file_browser_elts.drag_drop_file_in_drop_zone()

    assert file_browser_elts.file_information.find().text == 'sample-upload.txt', \
        "Expected sample-upload.txt to be the first file in Input Data"

    # TODO - Upload file to Output Data, need to deal with untracked directory


def test_dataset_file_browser(driver: selenium.webdriver, *args, **kwargs):
    """
    Test that a file can be dragged and dropped into data in a dataset.

    Args:
        driver
    """
    testutils.log_in(driver)
    testutils.GuideElements(driver).remove_guide()
    dataset_elts = testutils.DatasetElements(driver)
    dataset_title = dataset_elts.create_dataset(testutils.unique_dataset_name())
    logging.info(f"Navigating to Data for dataset: {dataset_title}")
    file_browser_elts = testutils.FileBrowserElements(driver)
    file_browser_elts.data_tab.wait().click()
    logging.info(f"Dragging and dropping file into Data for dataset: {dataset_title}")
    time.sleep(3)
    file_browser_elts.drag_drop_file_in_drop_zone()
    time.sleep(3)

    assert file_browser_elts.file_information.find().text == 'sample-upload.txt', \
        "Expected sample-upload.txt to be the first file in Data"

