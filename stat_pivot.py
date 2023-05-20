import auri
import pandas as pd
from pathlib import Path

output = Path("output")
dfs = {
    file.stem: pd.read_csv(file, index_col=0, usecols=range(1, 8))
    for file in output.glob("*.csv")
}

# print(dfs[0].합계)
# print(dfs[0].sum()[1:])

df_sido = pd.concat(
    [df.합계.to_frame(name=key).transpose().sort_index() for key, df in dfs.items()]
)
df_use = pd.concat(
    [
        df.sum()[1:].to_frame(name=key).transpose().sort_index()
        for key, df in dfs.items()
    ]
)

print(df_sido)
print(df_use)

df_sido.to_csv(f"output/completion_sido.csv", encoding="utf-8-sig")
df_use.to_csv(f"output/completion_use.csv", encoding="utf-8-sig")
