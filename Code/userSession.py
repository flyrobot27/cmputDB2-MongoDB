try:
    from pymongo import MongoClient
    import systemFunctions
    import re
    import json
    from multiprocessing import Pool, TimeoutError
    import multiprocessing
except ImportError as e:
    print("Error: Compulsory package missing:",e)
    print("Please ensure requirements are satisfied.")
    exit(1)

def question_actions(client, db, userID, searchResult):
    ''' Function Answer, List answers, action-vote'''
    columnNames = ["Post no.", "Title", "CreationDate", "Score", "AnswerCount"]
    displayStart = 0

    result = [[r["Title"], r["CreationDate"], r["Score"], r["AnswerCount"]] for r in searchResult]
    result = sorted(result, key=lambda x: x[2], reverse=True)

    result = [[i, *result[i - 1]] for i in range(1, len(result) + 1)]
    
    systemFunctions.display_result(columnNames, result, displayStart)


def __convert_to_string(item):
    ''' convert dict to string '''
    return json.dumps(item, sort_keys=True)

def __convert_to_dict(item):
    ''' convert string to dict '''
    return json.loads(item)

def search_question(client, db, userID, keywords):
    ''' Search all matching questions given keywords '''

    searchResult = set()
    collection_posts = db["Posts"]
    for kw in keywords:
        kw = kw.strip()
        findrgx = re.compile(".*" + kw + ".*", re.IGNORECASE)
        cpuava = int (multiprocessing.cpu_count()) - int(multiprocessing.cpu_count() / 4) + 1
        with Pool(cpuava) as p:  # using multithreading module to speed up the process
            # find matchings in Title
            result_title = collection_posts.find({"$and": [{"PostTypeId": "1", "Title": findrgx}]})
            result_title = set(p.map(__convert_to_string, result_title))

            # find matchings in Body
            result_body = collection_posts.find({"$and": [{"PostTypeId": "1", "Body": findrgx}]})
            result_body = set(p.map(__convert_to_string, result_body))

            # find matchings in Tags
            result_tags = collection_posts.find({"$and": [{"PostTypeId": "1", "Tags": findrgx}]})
            result_tags = set(p.map(__convert_to_string, result_tags))

        searchResult = searchResult.union(result_title.union(result_body.union(result_tags)))

    with Pool(4) as p:
        returnResult = list(p.map(__convert_to_dict, searchResult))

    return returnResult

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
    tags = input(">>> ")
    if tags != '':
        tags = tags.split(",")
        tags = list(set(["<" + t.lstrip().rstrip() + ">" for t in tags]))  # Convert it into a set to remove duplicates
        print("Please review your tags:")
        print(tags)

    else:
        tags = None
        print("No tag will be added.")
    
    # Prompt user to confirm post
    print()
    ans = input("Confirm Post? (y/N) ").strip()
    if ans not in ['y', 'Y', "yes", "Yes", "YES"]:
        print("Post Discarded")
        return

    print("Posting...")
    # obtain collection Posts
    collection_posts = db["Posts"]

    # Assign PID
    maxPID = collection_posts.find_one(sort=[("_id", -1)])["_id"] # First find the document containing the max Id, then extract its Id field
    assert type(maxPID) == int, "maxPID type error (maxPID = {})".format(maxPID)

    newId = maxPID + 1
    posts_row["_id"] = newId

    posts_row["PostTypeId"] = "1" # Post type = Question
    posts_row["CreationDate"] = systemFunctions.get_currentTime()
    posts_row["Score"] = 0
    posts_row["ViewCount"] = 0
    posts_row["Body"] = body
    if userID:
        posts_row["OwnerUserId"] = userID
    
    posts_row["Title"] = title

    # Tag column are added only if user supplied them
    if tags != None:
        posts_row["Tags"] = ''.join(tags)

    # initialize Answer count and comment count
    posts_row["AnswerCount"] = 0
    posts_row["CommentCount"] = 0

    # set content license
    posts_row["ContentLicense"] = "CC BY-SA 2.5"

    # insert into Posts collection
    collection_posts.insert_one(posts_row)

    # inserting tags into Tags collection
    if tags == None:
        return
    else:
        collection_tags = db["Tags"]
        for t in tags:
            # Remove < >
            t = t.replace('<','').replace('>','')

            # Find the tag with the tagname. using regular expression for case insensitivity
            result = collection_tags.find_one({"TagName": re.compile('^' + re.escape(t) + '$', re.IGNORECASE)})

            if not result: # if such tag did not exist, create such entry
                new_tag = dict()

                # Assign new ID
                maxID = collection_tags.find_one(sort=[("_id", -1)])["_id"]
                assert type(maxID) == int, "Tag ID not digit: (ID = {})".format(maxID)
                new_tag["_id"] = maxID + 1
                new_tag["TagName"] = t
                new_tag["Count"] = 1

                collection_tags.insert_one(new_tag)
            else:
                assert type(result["Count"]) == int, "Tag Count not digit (Count = {})".format(result["Count"])

                count = result["Count"] + 1
                collection_tags.update_one({"TagName": re.compile('^' + re.escape(t) + '$', re.IGNORECASE)}, {"$set" : {"Count": count}})
    
    result = collection_posts.find({"_id": newId})
    if result:
        print("\nSuccess\n")
    else:
        print("\nDatabase Error: Posting Unsuccessful\n")

    return
                

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
            # Prompt for post question
            post_question(client, db, userID)

        elif int(userInput) == 2:
            # Prompt for typing keywords and search
            print("Enter your keyboards (space separated):")
            keywords = input(">>> ").split()
            result = search_question(client, db, userID, keywords)
            question_actions(client, db, userID, result)

        elif int(userInput) == 3:
            # Quit
            print("\nReturning to Home Page")
            print("*-----------------------*")
            return
