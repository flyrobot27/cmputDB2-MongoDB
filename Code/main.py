try:
    import sys
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

    # Initialize the program
    try:
        # setup connection to MongoDB
        client, db = mongoSetup.global_init(portNo, dbName)

        # extract list of collections
        collist = db.list_collection_names()

        # THIS IS FOR DEBUGGING PURPOSE ONLY SO THAT I DON'T NEED TO REBUILD THE DATABASE EVERYTIME
        # COMMENT THIS OUT DURING DEMO
        if set(['Posts', 'Tags', 'Votes']).issubset(collist):
            raise NotImplementedError   # COMMENT THIS LINE OUT DURING DEMO TIME
            pass

        client, db, dbReturn = mongoSetup.db_init(client, db, collist)

    except IOError as e:
        print("Unable to locate necessary collection files:",e)
        exit(2)
    except KeyError as e:
        print("Incorrect Json format.")
        exit(1)
    except NotImplementedError:
        print("Oh God I don't want to build the database everytime I debug.")
        print("Bypassing...")

    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nUser Interrupted.\nGoodBye.")
        exit(0)
    except Exception as e:
        print("Fatal error:",e)
        exit(1)