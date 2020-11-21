try:
    import sys
    import os
    import json
    import mongoSetup
except ImportError as err:
    print("Import error: {}".format(err))
    exit(1)

def main():
    # obtain DB port number
    if len(sys.argv) != 2 or sys.argv[1] in ("help", "--help", "-h"):
        print("Usage: python3 main.py [MongoDB port number]")
        exit(0)
    portNo = sys.argv[1]
    dbName = "291db"

    # setup connection to MongoDB
    client, db = mongoSetup.global_init(portNo, dbName)

    # Check if collection Posts, Tags or Votes exists
    collist = db.list_collection_names()
    collection_posts = db['posts']
    collection_tags = db['tags']
    collection_votes = db['votes']

    if not set(['posts', 'tags', 'votes']).isdisjoint(collist):
        print("Cleaning up collections ('posts', 'tags', 'votes') ")
        collection_posts.delete_many({})
        collection_tags.delete_many({})
        collection_votes.delete_many({})
        print("Cleanup complete")
    else:
        print("No existing collections ('posts', 'tags', 'votes') detected.")

    print("Creating collection...")

    try:
        # locate path for Posts.json, Tags.josn and Votes.json
        baseDir = os.path.dirname(os.path.abspath(__file__))
        postjsonpath = os.path.join(baseDir, 'Posts.json')
        tagjsonpath = os.path.join(baseDir, 'Tags.json')
        votejsonpath = os.path.join(baseDir, 'Votes.json')

        if not (os.path.isfile(postjsonpath) and os.path.isfile(tagjsonpath) and os.path.isfile(votejsonpath)):
            raise IOError
        
        filesJsonName = [('Posts.json',postjsonpath), ('Tags.json',tagjsonpath), ('Votes.json',votejsonpath)]
        # Open posts.json first
        for f in filesJsonName:
            jsonName = f[0]
            jsonPath = f[1]
            with open(postjsonpath) as filejson:        # attempt to open json file
                filecollect = json.load(filejson)       # convert file into python dictionary
                filecollect = filecollect['posts']['row']   # extract documents
                ret = collection_posts.insert_many(filecollect) # store into database

            print("{} [OK]".format(jsonName))
        
        print("Database Loaded")

    except IOError as e:
        print("Unable to locate necessary collection files:",e)
        exit(2)
    except KeyError as e:
        print("Incorrect Json format.")
        exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nUser Interrupted.\nGoodBye.")
        exit(0)
    except Exception as e:
        print("Fatal error:",e)
        exit(1)