# Builtin imports
import logging
import time
import os
import shutil
from subprocess import Popen, PIPE

# Library imports
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Local packages
import testutils


# def project_merge_conflict(driver: selenium.webdriver, *args, **kwargs):
#     """
#         Generate merge conflict by two users uploading files with same file name but different content.
#
#         Args:
#             driver
#     """
#     # Project set up
#     username = testutils.log_in(driver)
#     time.sleep(2)
#     testutils.remove_guide(driver)
#     time.sleep(2)
#     project_title = testutils.create_project_without_base(driver)
#
#     # Python 3 minimal base
#     testutils.add_py3_min_base(driver)
#     wait = WebDriverWait(driver, 200)
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".flex>.Stopped")))
#
#     # Publish project
#     publish_elts = testutils.PublishProjectElements(driver)
#     publish_elts.publish_project_button.click()
#     publish_elts.publish_confirm_button.click()
#     time.sleep(2)
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".flex>.Stopped")))
#
#     # Add collaborator with admin permission
#     logging.info(f"Adding a collaborator with Admin permission to private project {project_title}")
#     publish_elts.collaborators_button.click()
#     time.sleep(2)
#     username2 = testutils.load_credentials(user_index=1)[0].rstrip()
#     print(username, username2)
#     publish_elts.collaborators_input.send_keys(username2)
#     publish_elts.select_permission_button.click()
#     publish_elts.select_admin_button.click()
#     publish_elts.add_collaborators_button.click()
#     time.sleep(2)
#     publish_elts.close_collaborators_button.click()
#
#     # Owner add file to input data, not sync
#     logging.info("Owner adding a file to the project")
#     with open('/tmp/sample.txt', 'w') as example_file:
#         example_file.write('xxx')
#     input_path = os.path.join(os.environ['GIGANTUM_HOME'], username, username, 'labbooks', project_title,
#                               'input')
#     shutil.copy(example_file.name, input_path)
#     time.sleep(2)
#     testutils.log_out(driver)
#
#     # Collaborator log in
#     logging.info(f"Logging in as {username2}")
#     testutils.log_in(driver, user_index=1)
#     time.sleep(2)
#     try:
#         testutils.remove_guide(driver)
#     except:
#         pass
#     time.sleep(2)
#     publish_elts.cloud_tab.click()
#     time.sleep(3)
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".RemoteLabbooks__panel-title")))
#
#     # Collaborator imports the project from cloud
#     publish_elts.import_first_cloud_project_button.click()
#     time.sleep(2)
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".flex>.Stopped")))
#
#     # Collaborator added a file using same name with different content
#     logging.info("Collaborator adding a file to the project")
#     with open('/tmp/sample.txt', 'w') as example_file:
#         example_file.write('yyy')
#     input_path = os.path.join(os.environ['GIGANTUM_HOME'], username2, username, 'labbooks', project_title,
#                               'input')
#     shutil.copy(example_file.name, input_path)
#     time.sleep(2)
#
#     # Collaborator sync
#     logging.info(f"Collaborator syncing project {project_title} to the cloud")
#     publish_elts.sync_project_button.click()
#     time.sleep(2)
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".flex>.Stopped")))
#     # log out
#     testutils.log_out(driver)
#
#     # Owner load the project and sync
#     logging.info(f"Logging in as {username}")
#     testutils.log_in(driver)
#     time.sleep(2)
#     try:
#         testutils.remove_guide(driver)
#     except:
#         pass
#     time.sleep(2)
#     driver.find_element_by_css_selector(f"a[href='/projects/{username}/{project_title}']").click()
#     time.sleep(5)
#     logging.info(f"Owner syncing project {project_title} to the cloud")
#     publish_elts.sync_project_button.click()
#     time.sleep(10)
#
#     return username, username2, project_title
#
#
# def test_merge_conflict_use_mine(driver: selenium.webdriver, *args, **kwargs):
#     """
#         Test that merge conflict is handled correctly by selecting 'use mine'.
#
#         Args:
#             driver
#     """
#     # generate merge conflict
#     username, username2, project_title = project_merge_conflict(driver)
#
#     # check that merge conflict is generated
#     assert driver.find_element_by_css_selector(".ForceSync__buttonContainer").is_displayed(),\
#         "Owner expected merge conflict"
#     # solve the merge conflict by using mine
#     logging.info("Solving the merge conflict using mine")
#     driver.find_element_by_xpath("//button[contains(text(), 'Use Mine')]").click()
#     wait = WebDriverWait(driver, 200)
#     wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".Footer__message-item > p"), "Sync complete"))
#     input_path = os.path.join(os.environ['GIGANTUM_HOME'], username, username, 'labbooks', project_title,
#                               'input')
#     with open(os.path.join(input_path, 'sample.txt'), 'r') as conflict_file:
#         assert conflict_file.read() == 'xxx', "The file content is expected to match 'xxx' "
#
#     # Owner deletes cloud project
#     publish_elts = testutils.PublishProjectElements(driver)
#     publish_elts.project_page_tab.click()
#     publish_elts.cloud_tab.click()
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".RemoteLabbooks__panel-title")))
#     testutils.delete_project_cloud(driver, project_title)
#
#
# def test_merge_conflict_use_theirs(driver: selenium.webdriver, *args, **kwargs):
#     """
#         Test that merge conflict is handled correctly by selecting 'use theirs'.
#
#         Args:
#             driver
#     """
#     # generate merge conflict
#     username, username2, project_title = project_merge_conflict(driver)
#
#     # check that merge conflict is generated
#     assert driver.find_element_by_css_selector(".ForceSync__buttonContainer").is_displayed(),\
#         "Owner expected merge conflict"
#
#     # solve the merge conflict by using theirs
#     logging.info("Solving the conflict by using theirs ")
#     driver.find_element_by_xpath("//button[contains(text(), 'Use Theirs')]").click()
#     wait = WebDriverWait(driver, 200)
#     wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".Footer__message-item > p"), "Sync complete"))
#     input_path = os.path.join(os.environ['GIGANTUM_HOME'], username, username, 'labbooks', project_title,
#                               'input')
#     with open(os.path.join(input_path, 'sample.txt'), 'r') as conflict_file:
#         assert conflict_file.read() == 'yyy', "The file content is expected to match 'yyy' "
#
#     # Owner deletes cloud project
#     publish_elts = testutils.PublishProjectElements(driver)
#     publish_elts.project_page_tab.click()
#     publish_elts.cloud_tab.click()
#     wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".RemoteLabbooks__panel-title")))
#     testutils.delete_project_cloud(driver, project_title)
#
