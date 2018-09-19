def test_db():
    try:
        name = 'test'
        client = mongodb_connect('mongodb://' + DB_HOST + ':27017')
        client.server_info()  # force connection, trigger error to be caught
        db = client.quip_comp
        collection_saved = db[name + '_features_td']  # name
        patch_feature_data = collections.OrderedDict()
        patch_feature_data['test'] = 'test'
        patch_feature_data['datetime'] = datetime.now()
        collection_saved.insert_one(patch_feature_data)
    except Exception as e:
        print('test_db: ', e)
        exit(1)

