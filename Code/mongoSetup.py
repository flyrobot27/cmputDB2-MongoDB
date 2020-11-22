try:
    import os
    import json
    from pymongo import MongoClient
    from multiprocessing import Pool, TimeoutError
except ImportError as e:
    print("Error: Compulsory package missing:",e)
    print("Please ensure requirements are satisfied.")
    exit(1)

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

def db_init(client, db, collist):
    ''' Build the database. Return the database and the return from database'''

    # Check if collection Posts, Tags or Votes exists
    collection_posts = db['Posts']
    collection_tags = db['Tags']
    collection_votes = db['Votes']

    if not set(['Posts', 'Tags', 'Votes']).isdisjoint(collist):
        print("Cleaning up collections ('Posts', 'Tags', 'Votes') ")
        collection_posts.drop()
        print("Posts    [OK]")
        collection_tags.drop()
        print("Tags     [OK]")
        collection_votes.drop()
        print("Votes    [OK]")
        print("Cleanup complete")
    else:
        print("No existing collections ('Posts', 'Tags', 'Votes') detected.")

    print("Creating collection...")

    # locate path for Posts.json, Tags.josn and Votes.json
    baseDir = os.path.dirname(os.path.abspath(__file__))
    postjsonpath = os.path.join(baseDir, 'Posts.json')
    tagjsonpath = os.path.join(baseDir, 'Tags.json')
    votejsonpath = os.path.join(baseDir, 'Votes.json')

    if not (os.path.isfile(postjsonpath) and os.path.isfile(tagjsonpath) and os.path.isfile(votejsonpath)):
        raise IOError
    
    filesJsonName = [
        ('Posts.json',postjsonpath, collection_posts, 'posts'), 
        ('Tags.json',tagjsonpath, collection_tags, 'tags'), 
        ('Votes.json',votejsonpath, collection_votes, 'votes')
    ]

    # Open posts.json first
    for f in filesJsonName:
        jsonName = f[0]
        print("{:<13}".format(jsonName), end='')

        jsonPath = f[1]
        collection = f[2]
        cName = f[3]
        with open(jsonPath, 'r') as filejson:      # attempt to open json file
            fileobject = json.load(filejson)[cName]['row']      # load file into memory
            for fo in fileobject:
                fo["_id"] = int(fo["Id"])
                fo.pop("Id", None)
            collection.insert_many(fileobject)          # store into database
        print("[OK]")
    
    print("Database Loaded")
    
    return client, db
