# https://realpython.com/introduction-to-mongodb-and-python/
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client.mydb
coll = db.objects
query = {}

# items = coll.find_one(query)
# print(items)

items = coll.find(query)
for item in items:
    print(item)

client.close()
