import logging
import requests
import sys
import os
import json
import time

import selenium
from selenium.webdriver.common.by import By


def test_edge_build_versions(driver: selenium.webdriver, *args, **kwargs):
    """
    Test that the requests edge build version matches the selenium edge build version.
    """
    host = f"{os.environ['GIGANTUM_HOST']}/api/ping"
    logging.info("Getting requests edge build version")
    r = requests.get(host)
    if r.status_code != 200:
        logging.error(f"Gigantum is not found at {host}")
        sys.exit(1)
    requests_edge_build_version = json.loads(r.text)
    logging.info("Getting selenium edge build version")
    driver.get(host)
    time.sleep(2)
    if driver.name == 'firefox':
       driver.find_element_by_css_selector("#rawdata-tab").click()
    selenium_edge_build_version = json.loads(driver.find_element_by_css_selector("pre").text)

    assert requests_edge_build_version == selenium_edge_build_version, \
        "requests edge build version does not match selenium edge build version"
