# TE/SyCLoPS tool: to directly output DetectNodes output txts to a single CSV file
# Author: Yushan Han
# Date: Jan 2026
import numpy as np
import pandas as pd
from datetime import datetime
import glob

input_file_list=sorted(glob.glob("/full_path_to_DetectNodes_output_files/*.txt"))

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
columns = ["ISOTIME"] + [f"var{i+1}" for i in range(n_data_cols)]

#Write CSV
df = pd.DataFrame(rows, columns=columns)
# Rename all columns depending on your data
df.columns = ["ISOTIME", "n_i", "n_j", "lon", "lat", "MSLP","MSLPCC20","MSLPCC55","WS","DEEPSHEAR","UPPTKCC","MIDTKCC","LOWTKCC",
                "Z500CC","VO500AVG","RH100MAX","RH850AVG","T850","Z850","ZS","U850DIFF","WS200PMX"] # Modify column names as needed
# Add track_id column for each row. Each row will have a unique track_id starting from 0
df.insert(0, "track_id", range(len(df)))
output_file = "/full_path_to_your_output_csv_files"
df.to_csv(output_file, index=False)
print(f"Saved {len(df)} rows to {output_file}")
