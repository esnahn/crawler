from pathlib import Path
import pandas as pd

### conditions

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

sido_dict = {
    "11": "서울",
    "26": "부산",
    "27": "대구",
    "28": "인천",
    "29": "광주",
    "30": "대전",
    "31": "울산",
    "36": "세종",
    "41": "경기",
    "42": "강원",
    "43": "충북",
    "44": "충남",
    "45": "전북",
    "46": "전남",
    "47": "경북",
    "48": "경남",
    "50": "제주",
}


def process_df(df: pd.DataFrame, sido, year, month):
    df = df.iloc[:, 1:]
    df["sidocode"] = sido
    df["sidoname"] = sido_dict[sido]
    df["year"] = year
    df["month"] = month
    df["yearmonth"] = f"{year:04d}{month:02d}"
    return df


dfs = []

for sido in sidos:
    for year in range(2003, 2022 + 1):
        for month in range(1, 12 + 1):
            filepath = f"output/sgg_sido{sido}_{year:04d}{month:02d}.csv"
            if not Path(filepath).exists():
                continue

            try:
                df = process_df(pd.read_csv(filepath), sido, year, month)
            except:
                raise

            if df is not None:
                dfs.append(df)
            else:
                print(f"no result on {sido, year, month}")

result_filepath = f"output/agg_sgg.csv"

result_df = pd.concat(dfs, ignore_index=True)
result_df.to_csv(result_filepath, encoding="utf-8-sig")

print("done")
