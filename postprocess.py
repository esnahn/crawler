import pandas as pd
import glob
import warnings
from tqdm import tqdm
from multiprocessing import Pool


def read_excel_wrapper(file_path):
    # Ignore a specific warning by its message
    warnings.filterwarnings(
        "ignore", message="Workbook contains no default style, apply openpyxl's default"
    )
    return pd.read_excel(file_path)


if __name__ == "__main__":
    # Pattern for matching file paths
    pattern = "output/bigkinds/NewsResult_*.xlsx"

    # Use glob to find all files that match the pattern
    file_paths = glob.glob(pattern)

    # Using Pool for parallel processing
    with Pool() as pool:
        dfs = list(
            tqdm(pool.imap(read_excel_wrapper, file_paths), total=len(file_paths))
        )

    # Concatenate the resulting DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df.to_parquet("output/bigkinds_combined.parquet")
