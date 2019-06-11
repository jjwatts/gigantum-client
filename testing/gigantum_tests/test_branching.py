import logging
import time
import os

import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import testutils
from testutils import graphql


def test_create_local_branch(driver: selenium.webdriver, *args, **kwargs):
    """
    Test the creation of a local branch.
    """
    r = testutils.prep_py3_minimal_base(driver)
    username, project_title = r.username, r.project_name
    branch_elts = testutils.BranchElements(driver)
    branch_elts.create_local_branch("test-branch")
    time.sleep(8)
    logging.info("Checking that you are on the new branch and that the new branch is local only")

    assert branch_elts.upper_left_branch_name.find().text == "test-branch", \
        "Expected to be on test-branch, upper left"
    assert branch_elts.upper_left_branch_local_only.find(), "Expected test-branch to be local only, upper left"

    branch_elts.manage_branches_button.wait().click()
    time.sleep(2)

    assert branch_elts.manage_branches_branch_name.find().text == "test-branch", \
        "Expected to be on test-branch, manage branches"
    assert branch_elts.manage_branches_local_only.find(), "Expected test-branch to be local only, manage branches"


def test_delete_file_local_branch(driver: selenium.webdriver, *args, **kwargs):
    """
    Test that a file created on the master branch, deleted in a local branch, and then merged back into the
    master branch does not appear in the master branch.
    """
    r = testutils.prep_py3_minimal_base(driver)
    username, project_title = r.username, r.project_name
    logging.info(f"Navigating to Input Data")
    driver.get(f"{os.environ['GIGANTUM_HOST']}/projects/{username}/{project_title}/inputData")
    time.sleep(2)
    logging.info(f"Adding a file to the master branch of project {project_title}")
    file_browser_elts = testutils.FileBrowserElements(driver)
    file_browser_elts.drag_drop_file_in_drop_zone()
    time.sleep(4)
    branch_elts = testutils.BranchElements(driver)
    branch_elts.create_local_branch("test-branch")
    time.sleep(8)
    logging.info(f"Deleting file in test-branch")
    file_browser_elts = testutils.FileBrowserElements(driver)
    file_browser_elts.check_file_check_box.find().click()
    file_browser_elts.delete_file_button.wait().click()
    file_browser_elts.confirm_delete_file_button.wait().click()
    time.sleep(2)
    branch_elts.switch_to_alternate_branch()
    branch_elts.merge_alternate_branch()
    logging.info(f"Checking that file deleted in test-branch does not appear in master branch")

    assert file_browser_elts.file_browser_empty.find(), \
        "Expected sample-upload.txt to not appear in master branch"


'''def test_favorite_file_local_branch(driver: selenium.webdriver, *args, **kwargs):
    """
    Test that a file created on the master branch, favorited in a local branch, and then merged back into the
    master branch is favorited in the master branch.
    """
    r = testutils.prep_py3_minimal_base(driver)
    username, project_title = r.username, r.project_name
    logging.info(f"Navigating to Input Data")
    driver.get(f"{os.environ['GIGANTUM_HOST']}/projects/{username}/{project_title}/inputData")
    time.sleep(2)
    logging.info(f"Adding a file to the master branch of project {project_title}")
    file_browser_elts = testutils.FileBrowserElements(driver)
    file_browser_elts.drag_drop_file_in_drop_zone()
    time.sleep(4)
    branch_elts = testutils.BranchElements(driver)
    branch_elts.create_local_branch("test-branch")
    time.sleep(8)
    logging.info(f"Favoriting file in test-branch")
    favorite_file_off_hover = ActionChains(driver).move_to_element(file_browser_elts.favorite_file_button_off.find())
    favorite_file_off_hover.perform()
    file_browser_elts.favorite_file_button_off.find().click()
    time.sleep(2)
    branch_elts.switch_to_alternate_branch()
    branch_elts.merge_alternate_branch()
    logging.info(f"Checking that file favorited in test-branch is favorited in master branch")

    assert file_browser_elts.favorite_file_button_on.find(), \
        "Expected sample-upload.txt to be favorited in master branch"'''
