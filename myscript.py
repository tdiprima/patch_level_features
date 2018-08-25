import sys
import pandas

# This program will take arguments:
# slide_name
# user_name
# tile_size
# db_host

program_name = sys.argv[0]
arguments = sys.argv[1:]
count = len(arguments)

# check command-line arguments
if count != 5:
    print 'Usage: python ' + program_name + ' slide_name user_name tile_size db_host'
    # sys.exit(1)

# temporarily using 1 input file
filename = 'input_demo.csv'
df = pandas.read_csv(filename)

for name, values in df.iteritems():
    print '{name}: {type}'.format(name=name, type=type(values[0]))
    # print '{name}: {value}'.format(name=name, value=values[0])
