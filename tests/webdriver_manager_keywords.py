# webdriver_manager_keywords.py
from webdriver_manager.chrome import ChromeDriverManager 
from robot.api.deco import keyword

@keyword("Get Chrome Driver")
def get_chrome_driver():
    driver_path = ChromeDriverManager().install()
    return driver_path