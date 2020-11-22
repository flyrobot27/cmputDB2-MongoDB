try:
    import os
    import ijson
    from pymongo import MongoClient
    from multiprocessing.dummy import Pool
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

def db_init_thread(f):
    ''' Thread for building each db '''

    jsonName = f[0]
    fstr = "Starting to load " + jsonName
    print(fstr)

    jsonPath = f[1]
    collection = f[2]
    cName = f[3]
    with open(jsonPath, 'r') as filejson:      # attempt to open json file
        exstr = cName + ".row.item"                   # extract collname.row.items
        fileobject = ijson.items(filejson, exstr)      # load file as generator

        # store into database as batches
        batch = list()
        i = 0
        MAX_BATCH_SIZE = 10000

        for fo in fileobject:
            fo["_id"] = int(fo["Id"])
            fo.pop("Id", None)
            batch.append(fo)
            i += 1
            if i >= MAX_BATCH_SIZE:  # max size of each batch reached
                collection.insert_many(batch)          # store batches
                del batch
                batch = list()
                i = 0

        collection.insert_many(batch)          # store remaining batches
                
    print("{} loaded".format(jsonName))

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

    # load database
    with Pool(3) as p:
        p.map(db_init_thread, filesJsonName)
        
    print("\n*** Database Loaded *** \n")
    
    return client, db
