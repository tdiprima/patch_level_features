from pymongo import MongoClient, errors


def get_composite_exec_id():
    """
    There is only one composite dataset (unique execution_id) in quip_comp
    database for each image.
    :return:
    """
    m_dict = {}
    try:
        client = mongodb_connect('mongodb://' + args["db_host"] + ':27017')
        client.server_info()  # force connection, trigger error to be caught
        db = client.quip_comp
        coll = db.metadata
        query = {"image.case_id": CASE_ID,
                 "provenance.analysis_execution_id": {'$regex': 'composite_dataset', '$options': 'i'}}
        m_dict = coll.find_one(query)
        client.close()
    except errors.ServerSelectionTimeoutError as err:
        print('Error in get_composite_exec_id', err)
        exit(1)
    return m_dict['provenance']['analysis_execution_id']


def mongodb_connect(client_uri):
    """
    Connection routine
    :param client_uri:
    :return:
    """
    try:
        return MongoClient(client_uri, serverSelectionTimeoutMS=1)
    except errors.ConnectionFailure:
        print("Failed to connect to server {}".format(client_uri))
        exit(1)


args = []
CASE_ID = ''
# Get exec_id for polygons.
# composite_exec_id = get_composite_exec_id()
