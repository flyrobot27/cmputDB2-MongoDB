try:
    import sys
    import mongoSetup
    import userSession
    import systemFunctions
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

        client, db, = mongoSetup.db_init(client, db, collist)

    except IOError as e:
        print("Unable to locate necessary collection files:",e)
        exit(2)
    except KeyError as e:
        print("Incorrect Json format.")
        exit(1)
    except NotImplementedError:
        print("Oh God I don't want to build the database everytime I debug.")
        print("Bypassing...")

    print("*-----------------------*")
    print("Welcome!")
    while True:
        print("Please Select an action:")
        print("1. Browse the Document Store")
        print("2. Quit")
        userInput = input("(1/2) >>> ").strip()
        if not userInput.isdigit() or int(userInput) not in [1,2]:
            print("\nError: Invalid Input\n")
            print("*-----------------------*")
        else:
            if int(userInput) == 1:
                userID = input("Enter user ID (Press Enter to skip)>>> ").strip()
                print("*-----------------------*")

                if userID == '': 
                    # anonymous session
                    userSession.session(client, db)
                else:
                    # print user report then start user session
                    systemFunctions.print_report(client, db, userID)
                    userSession.session(client, db, userID)
            elif int(userInput) == 2:
                print("GoodBye")
                exit(0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nUser Interrupted.\nGoodBye.")
        exit(0)
    except Exception as e:
        print("Fatal error:",e)
        exit(1)