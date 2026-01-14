# TE/SyCLoPS tool: to directly output DetectNodes output txts to a single CSV file
# Author: Yushan Han
# Date: Jan 2026
import numpy as np
import pandas as pd
from datetime import datetime
import glob

input_file_list=sorted(glob.glob("/path_to_DetectNodes_output_files/*.txt"))

rows = []
current_datetime = None

# open files in input_file_list one by one and concatenate the data
for input_file in input_file_list:
    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # Header line: year month day hour
            if len(parts) == 5:
                year, month, day, count, hour = map(int, parts)
                current_datetime = datetime(year, month, day, hour)
            # Data line
            else:
                values = [float(x) for x in parts]
                rows.append([current_datetime] + values)
                
# Create DataFrame once
n_data_cols = len(rows[0]) - 1
columns = ["datetime"] + [f"var{i+1}" for i in range(n_data_cols)]

#Write CSV
df = pd.DataFrame(rows, columns=columns)
# Rename all columns depending on your data
df.columns = ["datetime", "n_i", "n_j", "lon", "lat", ...]
output_file = "CNRM_all_data.csv"
df.to_csv(output_file, index=False)
print(f"Saved {len(df)} rows to {output_file}")
