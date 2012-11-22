import unittest
import test_helpers as helpers
import time



class testUserman(unittest.TestCase):
    def setUp(self):
        b = helpers.get_browser()
        b.get("https://localhost/userman")
        self.browser = b

    def login(self):
        username = self.browser.find_element_by_id("username")
        username.send_keys("teacher_coll1")

        password = self.browser.find_element_by_id("password")
        password.send_keys("facebees")

        login_button = self.browser.find_element_by_id("go")
        login_button.click()
        time.sleep(1)

    def test_landingpage_title(self):
        self.assertEqual(self.browser.title,"Student Robotics Userman")
        college = self.browser.find_element_by_id("college")
        self.assertFalse(college.is_displayed())

    def test_landingpage_login(self):
        self.login()

        college = self.browser.find_element_by_id("college")
        self.assertTrue(college.is_displayed())

    def test_landingpage_register(self):
        self.login()

        registration_link = self.browser.find_element_by_id("show-register")
        registration_link.click()
        register_users_div = self.browser.find_element_by_id("register-users")

        self.assertTrue("#register-users" in self.browser.current_url)
        self.assertTrue(register_users_div.is_displayed())

if __name__ == '__main__':
    unittest.main()