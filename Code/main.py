try:
    import sys
    import mongoSetup
except ImportError as err:
    print("Import error: {}".format(err))
    exit(1)

def main():
    # obtain DB file path
    if len(sys.argv) != 2 or sys.argv[1] in ("help", "--help", "-h"):
        print("Usage: python3 main.py [MongoDB port number]")
        exit(0)
    portNo = sys.argv[1]
    dbName = ""
    client, db = mongoSetup.global_init(portNo, dbName)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nUser Interrupted.\nGoodBye.")
        exit(0)
    except Exception as e:
        print("Fatal error:",e)
        exit(1)