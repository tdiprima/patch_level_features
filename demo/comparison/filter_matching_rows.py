"""
The script filters rows from one DataFrame (df1) based on matches in another DataFrame (df2) and saves the results.
"""

import pandas as pd

# First, the spreadsheets must agree.
df1 = pd.read_csv('bridge.csv')
df2 = pd.read_csv('me.csv')
df3 = pd.DataFrame()

# Loop through the "master" list.
for index, row in df1.iterrows():
    x1 = row['patch_min_x_pixel']
    y1 = row['patch_min_y_pixel']
    # Loop through all records in the second list.
    for index2, row2 in df2.iterrows():
        x2 = row['patch_min_x_pixel']
        y2 = row['patch_min_y_pixel']
        if x1 == x2 and y1 == y2:
            # If match is true then print row.
            df2 = df2.append(row)
            break

df3.to_csv('out.csv')
