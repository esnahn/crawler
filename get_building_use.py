import pandas as pd

import dask.dataframe as dd

# Load the datasets
commercial_df = dd.read_csv("data/commercial_sale_all.csv", dtype=str)
factory_df = dd.read_csv("data/factory_sale_all.csv", dtype=str)

# Concatenate the dataframes
commercial_usage_counts = (
    commercial_df["건축물주용도"].value_counts().to_frame().compute()
)
factory_usage_counts = factory_df["건축물주용도"].value_counts().to_frame().compute()

print("Commercial usage counts:")
print(commercial_usage_counts)
print("\nFactory usage counts:")
print(factory_usage_counts)

# Set MultiIndex with category and 건축물주용도
commercial_usage_counts.index.name = "건축물주용도"
commercial_usage_counts["category"] = "commercial"
commercial_usage_counts.set_index("category", append=True, inplace=True)
commercial_usage_counts = commercial_usage_counts.reorder_levels(
    ["category", "건축물주용도"]
)

factory_usage_counts.index.name = "건축물주용도"
factory_usage_counts["category"] = "factory"
factory_usage_counts.set_index("category", append=True, inplace=True)
factory_usage_counts = factory_usage_counts.reorder_levels(["category", "건축물주용도"])

# Concatenate the dataframes
combined_df = pd.concat([commercial_usage_counts, factory_usage_counts])
# combined_df = combined_df.sort_values(by=[combined_df.columns[0]], ascending=False)
combined_df = combined_df.groupby(level=0, group_keys=False).apply(
    lambda x: x.sort_values(by=x.columns[0], ascending=False)
)
print("Combined DataFrame:")
print(combined_df)

# Save to CSV
combined_df.to_csv("data/building_use.csv", index=True, encoding="utf-8-sig")
