import glob
import calendar
import time
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

use_ko = "연립다세대"
use_en = "multifamily"
use_tab_id = "xlsTab2"


# 1) Setup download directory
DOWNLOAD_DIR = os.path.join(os.getcwd(), "data", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 2) Configure Chrome options
options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": DOWNLOAD_DIR,  # 기본 다운로드 경로 설정 /쓰지 말고 \\로 사용할 것.
    "download.prompt_for_download": False,
    "profile.default_content_settings.popups": 0,
    "plugins.always_open_pdf_externally": True,
    "safebrowsing.enabled": False,
}
options.add_experimental_option("prefs", prefs)
# options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)

# 3) Define deal types
DEAL_TYPES = {
    "매매": {"code": "1", "label_en": "sale"},
    "전월세": {"code": "2", "label_en": "rent"},
}

try:
    # load page
    driver.get("https://rt.molit.go.kr/pt/xls/xls.do?mobileAt=")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "frm_xls")))
    time.sleep(3)

    # 1) 용도 탭 클릭
    driver.find_element(By.ID, use_tab_id).click()
    time.sleep(5)

    for deal_kor, deal in DEAL_TYPES.items():
        for year in range(2020, 2025):  # 2020–2024
            for month in range(1, 13):  # Jan–Dec
                # target filename
                tag = deal["label_en"]
                target = f"{use_en}_{tag}_{year}{month:02d}.csv"
                target_path = os.path.join(DOWNLOAD_DIR, target)

                # skip if already done
                if os.path.exists(target_path):
                    print(f"→ Skipped (exists): {target}")
                    continue

                # compute date range
                start_date = f"{year}-{month:02d}-01"
                last_day = calendar.monthrange(year, month)[1]
                end_date = f"{year}-{month:02d}-{last_day:02d}"

                # set deal code and dates via JS
                driver.execute_script(
                    "document.getElementById('srhDelngSecd').value = arguments[0];"
                    "document.getElementById('srhFromDt').value    = arguments[1];"
                    "document.getElementById('srhToDt').value      = arguments[2];",
                    deal["code"],
                    start_date,
                    end_date,
                )
                time.sleep(3)

                # trigger CSV download
                driver.find_element(
                    By.XPATH, "//button[@onclick='fnCSVDown()']"
                ).click()

                # wait for the timestamped download to land
                pattern = os.path.join(
                    DOWNLOAD_DIR, f"{use_ko}({deal_kor})_실거래가_*.csv"
                )
                for _ in range(60):
                    hits = glob.glob(pattern)
                    if hits:
                        # wait for the file to be realesed from the antivirus
                        time.sleep(5)

                        latest = max(hits, key=os.path.getmtime)
                        os.replace(latest, target_path)
                        print(f"✔ Downloaded: {target}")
                        break
                    time.sleep(1)
                else:
                    print(f"✖ Timeout: {deal_kor} {year}-{month:02d}")

                time.sleep(3)  # polite pause

finally:
    driver.quit()
