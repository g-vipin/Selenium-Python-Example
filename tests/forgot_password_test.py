import os

import allure
import pytest
from assertpy import assert_that

from tests.base_test import BaseTest


@allure.epic("Security")
@allure.story("Forgot Password Feature's Functionality")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.security
@allure.parent_suite("Custom parent suite")
@allure.suite("Custom suite")
@allure.sub_suite("Custom sub suite")
class TestForgotPassword(BaseTest):
    @allure.description("Forgot password with a valid email address")
    @allure.title("Forgot Password with valid email test")
    def test_valid_email(self, json_data: dict):
        self.about_page.click_login_link()
        self.login_page.click_forgot_password()
        self.forget_password_page.send_password_reset_link(os.getenv("EMAIL"))
        expected_success_message = json_data["forgot_password"]["success_message"]
        assert_that(expected_success_message).described_as(
            "success message"
        ).is_equal_to(self.forget_password_page.get_success_message())

    @allure.description("Forgot Password with invalid email address")
    @allure.title("Forgot Password with invalid email test")
    @pytest.mark.skipif(
        "'involve' in config.getoption('base_url')",
        reason="Conditional skip based on base url",
    )
    def test_invalid_email(self, excel_reader, json_data: dict):
        """This test is an example of a conditional skip based on base url."""
        emails = excel_reader.read_from_excel("Emails")
        self.about_page.click_login_link()
        self.login_page.click_forgot_password()
        self.forget_password_page.send_password_reset_link(emails[0])
        expected_error_message = json_data["forgot_password"]["error_message"]
        assert_that(expected_error_message).described_as("error message").is_equal_to(
            self.forget_password_page.get_invalid_email_message()
        )

    @allure.description("Exception catching")
    @allure.title("Exception test")
    @allure.link("https://github.com/allure-examples/", name="Allure Examples")
    @allure.issue(
        "https://github.com/allure-examples/allure-examples/issues/1", name="ISSUE-1"
    )
    @allure.testcase(
        "https://github.com/allure-examples/allure-examples/issues/2", name="TESTCASE-2"
    )
    def test_expected_exception_on_page_title(self):
        self.about_page.click_login_link()
        self.login_page.click_forgot_password()
        with pytest.raises(AssertionError) as e:
            assert_that(self.forget_password_page.get_page_title()).described_as(
                "page title"
            ).is_equal_to("something else")
        assert "AssertionError" in str(e)
