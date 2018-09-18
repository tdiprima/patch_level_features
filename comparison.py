import pandas as pd

df1 = pd.read_csv('a.csv')
print('df1', df1)
df2 = pd.read_csv('b.csv')
print('df2', df2)

x = df1[df1.apply(tuple, 1).isin(df2.apply(tuple, 1))]

print('type', type(x))

print('x', x)

# df = pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'f']})
# x = df.isin([1, 3, 12, 'a'])
# print('x', x)
