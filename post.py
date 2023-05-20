import calendar
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

import auri
from config import permit_stat_url

driver = webdriver.Edge()


def pick_date(elem: WebElement, year: int, month: int, day: int):
    # open the picker
    elem.click()
    time.sleep(0.1)

    # pick the year
    elem = driver.find_element(By.CLASS_NAME, "ui-datepicker-year")
    select = Select(elem)
    select.select_by_value(str(year))

    # pick the month
    elem = driver.find_element(By.CLASS_NAME, "ui-datepicker-month")
    select = Select(elem)
    # value starts at 0, 1 less than the month
    select.select_by_value(str(month - 1))

    # pick the day
    # should click the right one, instead previous or next month's one
    elem = driver.find_element(
        By.XPATH,
        f"//table[@class='ui-datepicker-calendar']//td[not(contains(@class, 'ui-datepicker-other-month'))]//a[text()='{day}']",
    )
    elem.click()


def get_table(driver: WebDriver):
    # 표 꺼내기
    parent_div = driver.find_element(By.ID, "gview_stsPurpsList")
    html = parent_div.get_attribute("outerHTML")

    # tables = table_parent_div.find_elements(By.CSS_SELECTOR, "table")

    # for table in tables:
    #     table_html = table.get_attribute("outerHTML")
    #     assert table_html.startswith(
    #         '<table class="ui-jqgrid-htable" style="width:985px" role="grid"'
    #     )

    # 데이터프레임 구성
    dfs = pd.read_html(html)

    # for i, df in enumerate(dfs):
    #     print(i)
    #     print(df)
    #     print(df.columns)
    #     print(df.index)

    assert dfs[0].columns.tolist() == ["지역", "합계", "주거용", "상업용", "공업용", "문교사회용", "기타"]
    assert dfs[1].loc[1, 0] == "서울특별시"
    assert dfs[1].loc[17, 0] == "제주특별자치도"

    df = dfs[1][1:]
    df.columns = dfs[0].columns.tolist()
    return df


def get_quarter(number):
    # proudly presented by ChatGPT
    if number in [1, 2, 3]:
        return 1
    elif number in [4, 5, 6]:
        return 2
    elif number in [7, 8, 9]:
        return 3
    elif number in [10, 11, 12]:
        return 4
    else:
        return None


def do_run(driver: WebDriver, year: int, month: int):
    # 조회 창 띄우기
    driver.get(permit_stat_url)

    # 진행구분 준공
    elem = driver.find_element(By.ID, "prs_gbn")
    select = Select(elem)
    select.select_by_value("useapr")

    # 지역단위 시도
    elem = driver.find_element(By.ID, "jiyeok_gbn")
    select = Select(elem)
    select.select_by_value("sido")

    # 자료구분 면적
    assert driver.find_element(By.XPATH, '//*[@id="down_gbn"]/option[1]').is_selected

    quarter = get_quarter(month)
    _, num_days = calendar.monthrange(year, month)

    # 기준년도
    elem = driver.find_element(By.ID, "data_day")
    select = Select(elem)
    select.select_by_value(f"{year}_{quarter}")

    # 조회기간
    elem = driver.find_element(By.ID, "day_s")
    pick_date(elem, year, month, 1)
    elem = driver.find_element(By.ID, "day_e")
    pick_date(elem, year, month, num_days)

    # 조회 실행
    driver.execute_script("search();")

    time.sleep(3)
    while (
        driver.find_element(By.ID, "load_stsPurpsList").value_of_css_property("display")
        == "block"
    ):
        time.sleep(1)

    # 결과 반환
    return get_table(driver)


for year in range(2013, 2022 + 1):
    for month in range(1, 12 + 1):
        try:
            df = do_run(driver, year, month)
        except:
            time.sleep(10)
            raise
        df.to_csv(f"output/{year:04d}{month:02d}.csv", encoding="utf-8-sig")

print("done")
