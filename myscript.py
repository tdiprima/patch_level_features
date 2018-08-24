import sys

program_name = sys.argv[0]
arguments = sys.argv[1:]
count = len(arguments)
print count

if count != 4 :
    print "Usage: python " + program_name + " slide_name user_name tile_size"
    sys.exit (1)

