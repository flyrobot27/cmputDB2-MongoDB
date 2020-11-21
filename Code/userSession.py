try:
    from pymongo import MongoClient
    import systemFunctions
except ImportError as e:
    print("Error: Compulsory package missing:",e)
    print("Please ensure requirements are satisfied.")
    exit(1)

def question_actions(client, db, userID, searchResult):
    pass

def search_post(client, db, userID):
    return []

def post_question(client, db, userID):
    ''' User will be prompt to an editor for typing the Question '''

    # Prompt user to create post
    title, body = systemFunctions.editor()

    print("Please Review your post:")
    print("Title:")
    print(title)
    print("Body:")
    print(body)

    posts_row = dict()  # initialize row for storing entry

    # Prompt user to tag their post
    print("\nPlease enter your tags. Use comma (,) to seperate the tags and press Enter to finish")
    print("You may also press enter to skip this step")
    tags = input(">>> ").lstrip().rstrip()
    if tags != '':
        tags = tags.split(",")
        tags = ["<" + t + ">" for t in tags]
        print("Please review your tags:")
        print(tags)

        # Tag column are added only if user supplied them
        posts_row["Tags"] = ''.join(tags)

    else:
        tags = None
        print("No tag will be added.")
    
    # Prompt user to confirm post
    print()
    ans = input("Confirm Post? (y/N) ").strip()
    if ans not in ['y', 'Y', "yes", "Yes", "YES"]:
        print("Post Discarded")
        return
    
    # Assign PID
    collection_posts = db["Posts"]
    maxPID = collection_posts.find_one(sort=[("Id", -1)])["Id"] # First find the document containing the max Id, then extract its Id field
    assert maxPID.isdigit(), "maxPID type error (maxPID = {})".format(maxPID)

    newId = int(maxPID) + 1
    posts_row["Id"] = str(newId)
    posts_row["PostTypeId"] = "1"
    if userID:
        posts_row["OwnerUserId"] = userID
    posts_row["Title"] = title
    posts_row["Body"] = body
    posts_row["ContentLicense"] = "CC BY-SA 2.5"


def session(client, db, userID=None):
    ''' User main page where they can post questions and search questions'''
    if userID is not None:
        print("Welcome! u/"+userID)
    else:
        print("Welcome!")
    while True:
        print("Please select an action:")
        print("1. Post a question")
        print("2. Search for a question")
        print("3. Return to home page")
        userInput = input("(1/2/3) >>> ").strip()
        if not userInput.isdigit() or int(userInput) not in [1,2,3]:
            print("\nError: Invalid Input\n")
        elif int(userInput) == 1:
            post_question(client, db, userID)
        elif int(userInput) == 2:
            result = search_post(client, db, userID)
            question_actions(client, db, userID, result)
        elif int(userInput) == 3:
            print("\nReturning to Home Page")
            print("*-----------------------*")
            return
