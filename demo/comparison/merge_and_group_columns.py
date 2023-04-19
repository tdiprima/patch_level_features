"""
This script groups rows from a DataFrame (df2) by a column, reshapes the data, and merges it with another DataFrame (df1).
You get a new table where each row from df1 is matched with all the extra grouped details from df2.
"""

import pandas as pd

df1 = pd.DataFrame({'Column1': [1, 2, 3, 4, 5],
                    'Column2': ['a', 'b', 'c', 'd', 'e'],
                    'Column3': ['r', 'u', 'k', 'j', 'f']})

df2 = pd.DataFrame({'Column1': [1, 1, 1, 2, 2, 3, 3], 'ColumnB': ['a', 'd', 'e', 'r', 'w', 'y', 'h']})

dfs = pd.DataFrame({})
for name, group in df2.groupby('Column1'):
    buffer_df = pd.DataFrame({'Column1': group['Column1'][:1]})
    i = 0
    for index, value in group['ColumnB'].iteritems():
        i += 1
        string = 'Column_' + str(i)
        buffer_df[string] = value

    dfs = dfs.append(buffer_df)

result = pd.merge(df1, dfs, how='left', on='Column1')
print(result)
