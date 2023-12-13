import calendar
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import webbrowser

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import SessionNotCreatedException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from config import url, login

# import pandas as pd
# import auri


output_dir = Path("output/bigkinds")


class State(Enum):
    UNKNOWN = auto()
    NOT_INIT = auto()
    NOT_LOGGEDIN = auto()
    DATEPICKER = auto()
    MEDIAPICKER = auto()
    SEARCH_WAIT = auto()
    SEARCH_RESULT = auto()
    DOWNLOAD_PANEL = auto()
    DOWNLOAD_ALERT = auto()
    DOWNLOAD_WAIT = auto()
    DOWNLOAD_COMPLETE = auto()


def get_state(driver: WebDriver, start_date, end_date):
    try:
        if not driver.current_url == url:
            return State.NOT_INIT

    except Exception as e:
        print("Error while checking the url:", e)
        return State.UNKNOWN

    try:
        # Wait for the button to be present
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.login-area-after"))
        )

        if not button.is_displayed():
            return State.NOT_LOGGEDIN

    except Exception as e:
        print("Error while checking login status:", e)
        return State.UNKNOWN

    ### logged in

    ### check the opened panel

    def check_opened(element_id):
        # Find the element by its ID
        element = driver.find_element(By.ID, element_id)

        # Get the class attribute of the element
        class_attribute = element.get_attribute("class")

        # check if it has 'open'
        return "open" in class_attribute.split()

    try:
        panel_ids = ["collapse-step-1", "collapse-step-2", "collapse-step-3"]
        level1_opened = []
        for panel_id in panel_ids:
            level1_opened.append(check_opened(panel_id))

    except Exception as e:
        print("Error while checking the panels' open status:", e)
        return State.UNKNOWN

    def check_visible(element):
        if not type(element) is WebElement:
            # Find the element by its ID
            element = driver.find_element(By.ID, element)

        # Get the value of the 'display' CSS property
        display_style = element.value_of_css_property("display")

        return not (display_style == "none")

    if level1_opened == [True, False, False]:
        # first panel is opened
        try:
            tab_ids = ["srch-tab1", "srch-tab2"]

            level2_opened = []
            for tab_id in tab_ids:
                level2_opened.append(check_visible(tab_id))

            if level2_opened == [True, False]:
                return State.DATEPICKER
            elif level2_opened == [False, True]:
                return State.MEDIAPICKER
            else:
                return State.UNKNOWN
        except Exception as e:
            print("Error while checking the tabs' open status:", e)
            return State.UNKNOWN

    elif level1_opened == [False, True, False]:
        # second panel is opened

        waiting_splash = "#collapse-step-2-body > div > div.data-result.loading-cont > div.news-loader.loading"

        try:
            element = driver.find_element(By.CSS_SELECTOR, waiting_splash)

            if check_visible(element):
                return State.SEARCH_WAIT
            else:
                return State.SEARCH_RESULT

        except NoSuchElementException():
            print("Is second panel opened? Element not found.")
            return State.UNKNOWN

    elif level1_opened == [False, False, True]:
        # third panel is opened

        try:
            # Find the 'a' element with the specific id and then locate its 'li' parent
            parent_element = driver.find_element(
                By.XPATH, '//a[@id="analytics-preview-tab"]/..'
            )

            # Check if the parent has the 'active' class
            is_active = "active" in parent_element.get_attribute("class")

            if not is_active:
                return State.UNKNOWN
        except:
            print("Is third panel opened? Tab not found.")
            return State.UNKNOWN

        try:
            alert = driver.switch_to.alert
            return State.DOWNLOAD_ALERT
        except:
            # no alert
            pass

        waiting_splash = "#analytics-data-download > div.data-down-scroll > div > div > div.news-loader.loading"
        try:
            element = driver.find_element(By.CSS_SELECTOR, waiting_splash)

            if check_visible(element):
                return State.DOWNLOAD_WAIT

        except NoSuchElementException():
            print("Is third panel opened? Element not found.")
            return State.UNKNOWN

        try:
            if not check_current_dates(driver) == (start_date, end_date):
                State.NOT_INIT
            if check_file_exists(start_date, end_date, output_dir):
                return State.DOWNLOAD_COMPLETE
        except:
            print("What file?")
            raise

        # ruled out everything else
        return State.DOWNLOAD_PANEL

    return State.UNKNOWN


def check_current_dates(driver):
    try:
        # Find the element by its id
        date_span = driver.find_element(By.ID, "footersearch_searchDate")

        # Extract the text from the <i> tag within the span
        date_text = date_span.find_element(By.TAG_NAME, "i").get_attribute("innerHTML")
        # print(date_text)

        # Splitting the string to get individual dates
        start_date_str, end_date_str = date_text.split(" ~ ")
        # print(start_date_str, end_date_str)

        # Converting the strings to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        return start_date, end_date
    except:
        print("What dates?")
        raise


def init():
    try:
        # download path option
        # print(output_dir.absolute())
        options = Options()  # from Edge
        prefs = {
            "download.default_directory": str(output_dir.absolute()),
            "profile.default_content_setting_values.automatic_downloads": 1,  # Allow multiple automatic file downloads
        }
        options.add_experimental_option("prefs", prefs)

        # use edge with option
        driver = webdriver.Edge(options=options)
        # Maximize the window
        driver.maximize_window()

        driver.get(url)

        time.sleep(3)
        return driver
    except SessionNotCreatedException as e:
        if (
            "This version of Microsoft Edge WebDriver only supports Microsoft Edge"
            in str(e)
        ):
            print("Maybe update WebDriver?")
            webbrowser.open_new(
                "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
            )

        raise e


# Function to check if a file for a given date exists
def check_file_exists(start_date, end_date, output_dir):
    file_name = (
        f"NewsResult_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.xlsx"
    )
    return (output_dir / file_name).exists()


def do_login(driver: WebDriver, start_date, end_date):
    def click_login_button():
        button_locator = (
            By.CSS_SELECTOR,
            "div.login-area > button.btn-login.login-modal-btn.login-area-before",
        )
        modal_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(button_locator)
        )
        modal_button.click()

    try:
        try:
            login_password_input = driver.find_element(By.ID, "login-user-password")
            if not login_password_input.is_displayed():
                click_login_button()
        except:
            click_login_button()

        wait = WebDriverWait(driver, 10)
        login_id_input = wait.until(
            EC.visibility_of_element_located((By.ID, "login-user-id"))
        )
        login_id_input.clear()
        login_id_input.send_keys(login.id_)

        login_password_input = driver.find_element(By.ID, "login-user-password")
        login_password_input.clear()
        login_password_input.send_keys(login.password)

        login_button = driver.find_element(By.ID, "login-btn")
        login_button.click()

        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "button.login-area-after")
            )
        )

    except Exception as e:
        print("login failed")
        print(e)
        return False

    if get_state(driver, start_date, end_date) in [
        State.UNKNOWN,
        State.NOT_INIT,
        State.NOT_LOGGEDIN,
    ]:
        return False
    else:
        return True


def open_date_picker(driver: WebDriver):
    selector = "div.tab1 a"
    link_element = driver.find_element(By.CSS_SELECTOR, selector)

    # Check if 'current' is not in the class attribute
    if "current" not in link_element.get_attribute("class"):
        # use js to send click
        script = f"document.querySelector('{selector}').click();"
        driver.execute_script(script)
        time.sleep(1)

    if "current" in link_element.get_attribute("class"):
        return True
    else:
        return False


def open_media_picker(driver: WebDriver):
    selector = "div.tab2 a"
    link_element = driver.find_element(By.CSS_SELECTOR, selector)

    # Check if 'current' is not in the class attribute
    if "current" not in link_element.get_attribute("class"):
        # use js to send click
        script = f"document.querySelector('{selector}').click();"
        driver.execute_script(script)
        time.sleep(1)

    if "current" in link_element.get_attribute("class"):
        return True
    else:
        return False


def open_setting_panel(driver: WebDriver):
    id_ = "collapse-step-1"
    element = driver.find_element(By.ID, id_)

    # Check if 'open' is not in the class attribute
    if "open" not in element.get_attribute("class"):
        # use js to send click
        script = f"document.querySelector('#{id_}').click();"
        driver.execute_script(script)
        time.sleep(1)

    if "open" in element.get_attribute("class"):
        return True
    else:
        return False


def open_download_panel(driver: WebDriver):
    id_ = "collapse-step-3"
    element = driver.find_element(By.ID, id_)

    # Check if 'open' is not in the class attribute
    if "open" not in element.get_attribute("class"):
        # use js to send click
        script = f"document.querySelector('#{id_}').click();"
        driver.execute_script(script)
        time.sleep(1)

    if "open" in element.get_attribute("class"):
        return True
    else:
        return False


def do_apply(driver: WebDriver):
    selector = "button.news-report-search-btn"
    # use js to send click
    script = f"document.querySelector('{selector}').click();"
    driver.execute_script(script)
    time.sleep(1)


def do_download(driver: WebDriver):
    selector = "button.news-download-btn"
    # use js to send click
    script = f"document.querySelector('{selector}').click();"
    driver.execute_script(script)

    waiting_splash = "#analytics-data-download > div.data-down-scroll > div > div > div.news-loader.loading"
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, waiting_splash))
    )
    time.sleep(1)


def dismiss_alert(driver: WebDriver):
    try:
        alert = driver.switch_to.alert
        if "20,000" in alert.text:
            alert.dismiss()
            return True
        else:
            alert.dismiss()
            return False
    except NoAlertPresentException:
        return False


def pick_dates(driver: WebDriver, start_date, end_date):
    # Find the input element by its ID
    # end date first
    input_element = driver.find_element(By.ID, "search-end-date")

    # focus
    input_element.click()
    time.sleep(0.5)

    # check calender input
    date_picker_div = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "ui-datepicker-div"))
    )

    # Input new text into the element
    for _ in range(12):
        input_element.send_keys(Keys.BACK_SPACE)
    input_element.send_keys(end_date.strftime("%Y-%m-%d"))
    time.sleep(0.5)
    input_element.send_keys(Keys.ENTER)
    time.sleep(0.5)

    # start date
    input_element = driver.find_element(By.ID, "search-begin-date")

    # focus
    input_element.click()
    time.sleep(0.5)

    # check calender input
    date_picker_div = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "ui-datepicker-div"))
    )

    # Input new text into the element
    for _ in range(12):
        input_element.send_keys(Keys.BACK_SPACE)
    input_element.send_keys(start_date.strftime("%Y-%m-%d"))
    time.sleep(0.5)
    input_element.send_keys(Keys.ENTER)
    time.sleep(0.5)
    input_element.send_keys(Keys.ENTER)
    time.sleep(0.5)

    # check the result
    if check_current_dates(driver) == (start_date, end_date):
        return True
    else:
        return False


def pick_media(driver: WebDriver, media_checkbox_ids, media_names):
    def click_checkbox(checkbox_id):
        # use js to send click
        script = f"document.querySelector('input#{checkbox_id}').click();"
        driver.execute_script(script)

    for checkbox_id in media_checkbox_ids:
        parent_li = driver.find_element(By.XPATH, f'//*[@id="{checkbox_id}"]/../..')
        if "active" in parent_li.get_attribute("class"):
            # uncheck first
            click_checkbox(checkbox_id)
            time.sleep(0.5)

        click_checkbox(checkbox_id)
        time.sleep(0.5)

    search_setting = driver.find_element(
        By.CSS_SELECTOR, "div.srch-sort"
    ).get_attribute("innerHTML")

    for media_name in media_names:
        if media_name not in search_setting:
            return False

    return True


media_ids = ["전국일간지", "방송사"]
media_names = [
    "경향신문",
    "국민일보",
    "내일신문",
    "동아일보",
    "문화일보",
    "서울신문",
    "세계일보",
    "조선일보",
    "중앙일보",
    "한겨레",
    "한국일보",
    "KBS",
    "MBC",
    "OBS",
    "SBS",
    "YTN",
]


# 시작 날짜와 종료 날짜 설정
# 1/1부터 11/30까지
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 11, 30)

# 각 날짜에 대해 파일이 존재하는지 확인하고, 없는 날짜만 정리
dates_to_do = []
for single_date in (
    start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)
):
    if not check_file_exists(single_date, single_date, output_dir):
        dates_to_do.append(single_date)

# print(dates_to_do)


driver = init()

try:
    for single_date in dates_to_do:
        while True:
            current_state = get_state(driver, single_date, single_date)

            if current_state in [State.UNKNOWN, State.NOT_INIT]:
                print("resetting...")
                driver = init()

                open_date_picker(driver)

            if current_state == State.NOT_LOGGEDIN:
                result = do_login(driver, single_date, single_date)
                if result:
                    open_date_picker(driver)
                else:
                    print("login failed. resetting...")
                    driver = init()

            if current_state == State.DATEPICKER:
                result = pick_dates(driver, single_date, single_date)
                if result:
                    open_media_picker(driver)

            if current_state == State.MEDIAPICKER:
                result = pick_media(driver, media_ids, media_names)

                if (not result) or (
                    check_current_dates(driver) != (single_date, single_date)
                ):
                    print("setting error. resetting...")
                    driver = init()
                else:
                    do_apply(driver)

            if current_state == State.SEARCH_WAIT:
                time.sleep(1)

            if current_state == State.SEARCH_RESULT:
                open_download_panel(driver)

            if current_state == State.DOWNLOAD_WAIT:
                time.sleep(1)

            if current_state == State.DOWNLOAD_PANEL:
                do_download(driver)

            if current_state == State.DOWNLOAD_ALERT:
                print(f"{single_date} has more than 20,000 articles! Ignoring...")
                dismiss_alert(driver)
                break

            if current_state == State.DOWNLOAD_COMPLETE:
                print(f"{single_date} done")
                open_setting_panel(driver)
                open_date_picker(driver)
                break

            time.sleep(0.5)
finally:
    time.sleep(10)
    driver.quit()
