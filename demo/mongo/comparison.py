from __future__ import print_function
import pandas as pd
import csv

df1 = pd.read_csv('output.csv')
my_data = {}


def get_iterator(dict1):
    """
    Because dict.iterkeys(), dict.iteritems() and dict.itervalues()
    methods are not available in py3.
    :param dict1:
    :return:
    """
    try:
        # Python 2
        iter_obj = dict1.iteritems()
    except AttributeError:
        # Python 3
        iter_obj = iter(dict1.items())

    return iter_obj


# df["weight"].mean()
iter_obj = get_iterator(df1)
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

print(my_data)

# f = open('mycsvfile.csv', 'wb')
# keys, values = zip(*my_data.items())
# print(f, end="", file=depend)
# print >> f, ", ".join(keys)
# print >> f, ", ".join(values)
# f.close()

# with open('mycsvfile.csv', 'wb') as f:  # Just use 'w' mode in 3.x
#     w = csv.DictWriter(f, my_data.keys())
#     w.writeheader()
#     w.writerow(my_data)
# f.close()

try:
    df2 = pd.DataFrame.from_records(my_data)
    df2.to_csv('validation.csv')
except ValueError as err:
    with open("my_output_file.txt", "w") as f:
        writer = csv.writer(f)
        writer.writerows(my_data)
