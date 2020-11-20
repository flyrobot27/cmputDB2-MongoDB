from pymongo import MongoClient

def global_init(portNo, dbName):
    ''' initialize connection to MongoDB. Return db and client'''

    assert type(portNo) == str, "portNo is not str"

    portNo = portNo.strip()
    if not portNo.isdigit():
        raise ValueError("Port Number must be integers.")
    else:
        portNo = int(portNo)
    
    dbpath = 'mongodb://localhost:{}'.format(portNo)
    client = MongoClient(dbpath)
    db = client[dbName]
    return client, db