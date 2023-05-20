import auri
import pandas as pd
from pathlib import Path

output = Path("output")

## 시도

dfs = {
    file.stem: pd.read_csv(file, index_col=0, usecols=range(1, 8))
    for file in output.glob(("[0-9]" * 6) + ".csv")
}

df_sido = pd.concat(
    [df.합계.to_frame(name=key).transpose() for key, df in dfs.items()]
).sort_index()

# print(df_sido)
df_sido.to_csv(f"output/completion_sido.csv", encoding="utf-8-sig")


## 전국
dfs = {
    file.stem[-6:]: pd.read_csv(file, index_col=0, usecols=range(1, 8))
    for file in output.glob("total_" + ("[0-9]" * 6) + ".csv")
}
# print(list(dfs.keys()))

df_use = pd.concat(
    [df.iloc[:, 1:].rename(index={"전국": key}) for key, df in dfs.items()]
).sort_index()

print(df_use)
df_use.to_csv(f"output/completion_use.csv", encoding="utf-8-sig")

df_total = pd.concat(
    [df.합계.to_frame(name=key).transpose() for key, df in dfs.items()]
).sort_index()

print(df_total)
df_total.to_csv(f"output/completion_total.csv", encoding="utf-8-sig")
