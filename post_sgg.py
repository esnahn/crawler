import calendar
import re
import time
from pathlib import Path

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
    time.sleep(0.1)

    select.select_by_value(str(year))
    time.sleep(0.1)

    # pick the month
    elem = driver.find_element(By.CLASS_NAME, "ui-datepicker-month")
    select = Select(elem)
    time.sleep(0.1)

    # value starts at 0, 1 less than the month
    select.select_by_value(str(month - 1))
    time.sleep(0.1)

    # pick the day
    # should click the right one, instead previous or next month's one
    elem = driver.find_element(
        By.XPATH,
        f"//table[@class='ui-datepicker-calendar']//td[not(contains(@class, 'ui-datepicker-other-month'))]//a[text()='{day}']",
    )
    elem.click()
    time.sleep(0.1)


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
    # assert dfs[1].loc[1, 0] == "서울특별시"

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


def do_run(driver: WebDriver, sido: str, year: int, month: int):
    quarter = get_quarter(month)
    _, num_days = calendar.monthrange(year, month)

    # 세종 출범 이전 예외처리
    if sido == "36" and (year < 2012 or (year == 2012 and quarter <= 2)):
        return None

    # 조회 창 띄우기
    driver.get(permit_stat_url)

    # 진행구분 준공
    elem = driver.find_element(By.ID, "prs_gbn")
    select = Select(elem)
    select.select_by_value("useapr")

    # 지역단위 시군구
    elem = driver.find_element(By.ID, "jiyeok_gbn")
    select = Select(elem)
    select.select_by_value("sigungu")
    time.sleep(0.1)

    # 시도 선택
    elem = driver.find_element(By.ID, "sido_cd")
    select = Select(elem)
    select.select_by_value(sido)

    # 자료구분 면적
    assert driver.find_element(By.XPATH, '//*[@id="down_gbn"]/option[1]').is_selected

    # 기준년도
    elem = driver.find_element(By.ID, "data_day")
    select = Select(elem)
    if year >= 2013:
        select.select_by_value(f"{year}_{quarter}")
    elif year == 2012 and quarter >= 3:
        select.select_by_value(f"{year}_{quarter}")
    else:
        # use 2012 2th q for older data
        select.select_by_value(f"2012_2")

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


sidos = [
    "11",  # 서울
    "26",  # 부산
    "27",  # 대구
    "28",  # 인천
    "29",  # 광주
    "30",  # 대전
    "31",  # 울산
    "36",  # 세종
    "41",  # 경기
    "42",  # 강원
    "43",  # 충북
    "44",  # 충남
    "45",  # 전북
    "46",  # 전남
    "47",  # 경북
    "48",  # 경남
    "50",  # 제주
]

for sido in sidos:
    for year in range(2003, 2022 + 1):
        for month in range(1, 12 + 1):
            filepath = f"output/sgg_sido{sido}_{year:04d}{month:02d}.csv"
            if Path(filepath).exists():
                continue

            try:
                df = do_run(driver, sido, year, month)
            except:
                time.sleep(10)
                raise

            if df is not None:
                df.to_csv(filepath, encoding="utf-8-sig")
            else:
                print(f"no result on {sido, year, month}")

print("done")
