# https://realpython.com/introduction-to-mongodb-and-python/
from pymongo import MongoClient, errors


def mongodb_connect(client_uri):
    try:
        return MongoClient(client_uri, serverSelectionTimeoutMS=1)
    except errors.ConnectionFailure:
        print("Failed to connect to server {}".format(client_uri))
        exit(1)


try:
    client = mongodb_connect('mongodb://localhost:27017')
    client.server_info()  # force connection, trigger error to be caught

    db = client.mydb
    coll = db.objects
    query = {}

    # items = coll.find_one(query)
    # print(items)

    items = coll.find(query)
    for item in items:
        print(item)

    client.close()

except errors.ServerSelectionTimeoutError as err:
    print(err)
    exit(1)
