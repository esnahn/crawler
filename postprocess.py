import pandas as pd
import glob
import warnings
from tqdm import tqdm
from multiprocessing import Pool
from pathlib import Path


def process_excel(file_path, dir_to):
    # Ignore a specific warning by its message
    warnings.filterwarnings(
        "ignore", message="Workbook contains no default style, apply openpyxl's default"
    )

    original_path = Path(file_path)
    filename = original_path.with_suffix("").name

    df = pd.read_excel(file_path, dtype={"뉴스 식별자": str, "일자": str})
    df.to_parquet(dir_to / (filename + ".parquet"))
    return True


dir_to = Path("output/bigkinds_processed")


def wrapper(file_path):
    return process_excel(file_path, dir_to)


if __name__ == "__main__":
    dir_to.mkdir(parents=True, exist_ok=True)

    # Pattern for matching file paths
    pattern = "output/bigkinds/NewsResult_*.xlsx"

    # Use glob to find all files that match the pattern
    file_paths = glob.glob(pattern)

    # Using Pool for parallel processing
    with Pool() as pool:
        results = list(tqdm(pool.imap(wrapper, file_paths), total=len(file_paths)))

    # # Concatenate the resulting DataFrames
    # combined_df = pd.concat(dfs, ignore_index=True)
    # combined_df.to_parquet("output/bigkinds_combined.parquet")
