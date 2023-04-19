# Generates max, mean, and standard deviation from computed feature value comparison and writes the results to a CSV file.
from __future__ import print_function

import csv

import pandas as pd

# input_file = 'output.csv'
# output_file = 'validation.csv'
input_file = 'output1.csv'
output_file = 'validation1.csv'

df1 = pd.read_csv(input_file)
my_data = {}

# df["weight"].mean()
iter_obj = iter(df1.items())
count = 0
for name, values in iter_obj:
    count += 1
    if count > 4:
        # print('{name}: {type}'.format(name=name, type=type(values[0])))
        try:
            data = {}
            max = df1[name].max()
            mean = df1[name].mean()
            std = df1[name].std()
            data[name] = {'max_difference': max, 'mean_difference': mean, 'standard_deviation': std}
            my_data.update(data)
        except ValueError as err:
            max = 0
            mean = 0
            std = 0
            print(name, err)

# print(my_data)

try:
    df2 = pd.DataFrame.from_records(my_data)
    df2.to_csv(output_file)
    print("Writing complete")
except ValueError as err:
    print('An error occurred. Attempting to write to text file...')
    with open("my_output_file.txt", "w") as f:
        writer = csv.writer(f)
        writer.writerows(my_data)
    print('Done')

exit(0)
