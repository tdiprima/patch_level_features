# https://realpython.com/introduction-to-mongodb-and-python/
from pymongo import MongoClient, errors
import datetime

DB_HOST = 'mongodb://localhost:27017'


def mongodb_connect(client_uri):
    try:
        return MongoClient(client_uri, serverSelectionTimeoutMS=1)
    except errors.ConnectionFailure:
        print("Failed to connect to server {}".format(client_uri))
        exit(1)


try:
    client = mongodb_connect(DB_HOST)
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


def test_db():
    try:
        name = 'test'
        client = mongodb_connect('mongodb://' + DB_HOST + ':27017')
        client.server_info()  # force connection, trigger error to be caught
        db = client.quip_comp
        collection_saved = db[name + '_features_td']  # name
        # patch_feature_data = collections.OrderedDict()
        patch_feature_data = {}
        patch_feature_data['test'] = 'test'
        patch_feature_data['datetime'] = datetime.now()
        collection_saved.insert_one(patch_feature_data)
    except Exception as e:
        print('test_db: ', e)
        exit(1)
