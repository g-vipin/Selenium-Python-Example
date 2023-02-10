import json
from datetime import datetime

import allure
import requests
from git import Repo
from pytest import fixture, hookimpl
from selenium import webdriver

from globals.dir_global import ROOT_DIR
from pages.about_page import AboutPage
from pages.forgot_password_page import ForgotPasswordPage
from pages.login_page import LoginPage
from pages.project_edit_page import ProjectEditPage
from pages.project_type_page import ProjectTypePage
from pages.projects_page import ProjectsPage
from pages.templates_page import TemplatesPage
from utils.config_parser import AllureEnvironmentParser
from utils.config_parser import ConfigParserIni


# reads parameters from pytest command line
def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome", help="browser that the automation will run in")


def get_public_ip() -> str:
    return requests.get("http://checkip.amazonaws.com").text.rstrip()


@fixture(scope="session")
def prep_properties():
    return ConfigParserIni("props.ini")


@fixture(autouse=True, scope="session")
# fetch browser type and base url then writes a dictionary of key-value pair into allure's environment.properties file
def write_allure_environment(prep_properties):
    yield
    repo = Repo(ROOT_DIR)
    env_parser = AllureEnvironmentParser("environment.properties")
    env_parser.write_to_allure_env(
        {
            "Browser": driver.name,
            "Driver_Version": driver.capabilities['browserVersion'],
            "Base_URL": base_url,
            "Commit_Date": datetime.fromtimestamp(repo.head.commit.committed_date).strftime('%c'),
            "Commit_Message": repo.head.commit.message.strip(),
            "Commit_Id": repo.head.object.hexsha,
            "Commit_Author_Name": repo.head.commit.author.name,
            "Branch": repo.active_branch.name
        })


# https://stackoverflow.com/a/61433141/4515129
@fixture
# Instantiates Page Objects
def pages():
    about_page = AboutPage(driver)
    projects_page = ProjectsPage(driver)
    forgot_password_page = ForgotPasswordPage(driver)
    login_page = LoginPage(driver)
    project_type_page = ProjectTypePage(driver)
    templates_page = TemplatesPage(driver)
    project_edit_page = ProjectEditPage(driver)
    return locals()


@fixture(autouse=True)
def create_driver(write_allure_environment, prep_properties, request):
    global browser, base_url, driver, chrome_options
    browser = request.config.option.browser
    base_url = prep_properties.config_section_dict("Base Url")["base_url"]

    if browser in ("chrome", "chrome_headless"):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
    if browser == "firefox":
        driver = webdriver.Firefox()
    elif browser == "chrome_headless":
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(5)
    driver.maximize_window()
    driver.get(base_url)
    yield
    if request.node.rep_call.failed:
        allure.attach(body=driver.get_screenshot_as_png(), name="Screenshot",
                      attachment_type=allure.attachment_type.PNG)
        allure.attach(body=get_public_ip(), name="public ip address", attachment_type=allure.attachment_type.TEXT)
        allure.attach(body=json.dumps(driver.get_cookies(), indent=4), name="Cookies",
                      attachment_type=allure.attachment_type.JSON)
        allure.attach(body=json.dumps(
            {item[0]: item[1] for item in driver.execute_script("return Object.entries(sessionStorage);")}, indent=4),
            name="Session Storage", attachment_type=allure.attachment_type.JSON)
        allure.attach(body=json.dumps(
            {item[0]: item[1] for item in driver.execute_script("return Object.entries(localStorage);")}, indent=4),
            name="Local Storage", attachment_type=allure.attachment_type.JSON)
        allure.attach(body=json.dumps(driver.get_log("browser"), indent=4), name="Console Logs",
                      attachment_type=allure.attachment_type.JSON)
        allure.attach(body=json.dumps(
            create_unified_list([json.loads(log["message"])["message"] for log in driver.get_log("performance")]),
            indent=4), name="Network Logs",
            attachment_type=allure.attachment_type.JSON)
    driver.quit()


@hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()
    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, f"rep_{rep.when}", rep)


def create_unified_list(data):
    # Create a dictionary to store the unified items
    unified_items = {}

    # Loop through the data list
    # Loop through the data list
    for item in data:
        method = item.get("method")
        params = item.get("params")
        if params.get("type") == "XHR":
            request_id = params["requestId"]
            if request_id in unified_items:
                # If the requestId already exists in the dictionary, update the existing entry
                unified_item = unified_items[request_id]
                if method == "Network.responseReceived":
                    unified_item["response"] = item
                elif method == "Network.requestWillBeSent":
                    unified_item["request"] = item
            else:
                # If the requestId does not exist in the dictionary, add a new entry
                unified_item = {}
                if method == "Network.responseReceived":
                    unified_item["response"] = item
                elif method == "Network.requestWillBeSent":
                    unified_item["request"] = item
                unified_items[request_id] = unified_item

    # Return the unified items as a list
    return list(unified_items.values())
