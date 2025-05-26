import glob
from dask.delayed import delayed
import dask.dataframe as dd
import pandas as pd
import os

input_pattern = "data/downloads/apart_rent_*.csv"
output_path = "data/apart_rent_all.csv"

# 1) 소스 파일 목록
file_paths = glob.glob(input_pattern)
if not file_paths:
    raise RuntimeError(f"파일을 찾을 수 없습니다: {input_pattern}")

# 2) 첫 파일에서 동적 헤더 위치 탐색 및 메타(컬럼) 추출
first = file_paths[0]
header_idx_first = None
with open(first, "r", encoding="cp949") as f:
    for i, line in enumerate(f):
        if line.startswith('"NO","시군구"'):
            header_idx_first = i
            break
if header_idx_first is None:
    raise ValueError(f"헤더 행을 찾지 못했습니다: {os.path.basename(first)}")

meta = pd.read_csv(
    first,
    skiprows=header_idx_first,
    nrows=0,
    encoding="cp949",
    thousands=",",
    na_values="-",  # uses doublequoted hyphen for NA
    dtype=str,
)


# 3) 각 파일을 dask.delayed로 읽기
@delayed
def read_apart(fp):
    hdr = None
    with open(fp, "r", encoding="cp949") as f:
        for j, line in enumerate(f):
            if line.startswith('"NO","시군구"'):
                hdr = j
                break
    if hdr is None:
        raise ValueError(f"헤더 행을 찾지 못했습니다: {os.path.basename(fp)}")
    return pd.read_csv(
        fp, skiprows=hdr, header=0, encoding="cp949", thousands=",", na_values="-", dtype=str
    )


delayed_dfs = [read_apart(fp) for fp in file_paths]

# 4) dask DataFrame으로 변환·병합
ddfs = [dd.from_delayed(d, meta=meta) for d in delayed_dfs]
merged = dd.concat(ddfs, interleave_partitions=True)

# 5) 결과 저장 (utf-8-sig)
merged.to_csv(output_path, single_file=True, index=False, encoding="utf-8-sig")

print(f"✅ 병합 완료 — {len(file_paths)}개 파일 → {output_path}")
