import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import time


def get_contents(url):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "lxml")
    div = soup.find("div", attrs={"class": "textType02"})
    return div.text


df = pd.read_csv("law_filtered.csv")
### read latest csv file to resume
# df = pd.read_csv('law_filled_xxx.csv')

if "제안이유및주요내용" not in df.columns:
    df["제안이유및주요내용"] = pd.Series(dtype=str)

url_index = df.columns.get_loc("주요내용")
contents_index = df.columns.get_loc("제안이유및주요내용")

for line in range(len(df)):
    print(f"start item {line}...", end="")

    if df.iat[line, contents_index] is np.nan or not df.iat[line, contents_index]:
        url = df.iat[line, url_index]
        if url is not np.nan and str(url).startswith("http"):
            print("fetching...", end="")
            df.iat[line, contents_index] = get_contents(url)

    if not line % 100:
        print("saving...", end="")
        df.to_csv(f"law_filled_{line}.csv", encoding="utf-8-sig")

    time.sleep(0.1)
    print("done")

df.to_csv(f"law_filled.csv", encoding="utf-8-sig")
