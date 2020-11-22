try:
    from pymongo import MongoClient
    import systemFunctions
    import re
    import json
    from multiprocessing.dummy import Pool
    from functools import partial
    import multiprocessing
except ImportError as e:
    print("Error: Compulsory package missing:",e)
    print("Please ensure requirements are satisfied.")
    exit(1)

def answer_question(client, db, posts):
    ''' answer a question '''

def question_actions(client, db, userID, searchResult):
    ''' Function Answer, List answers, action-vote'''
    columnNames = ["Post ID", "Title", "CreationDate", "Score", "AnswerCount"]
    displayStart = 0

    result_dict = dict()
    for r in searchResult:
        key = r["_id"]
        del r["_id"]
        result_dict[key] = r

    searchResult = result_dict
    del result_dict

    avaliable_posts = list(searchResult.keys())
    
    result = [[key, item["Title"], item["CreationDate"], item["Score"], item["AnswerCount"]] for key, item in searchResult.items()]

    result = sorted(result, key=lambda x: x[2], reverse=True)
    systemFunctions.display_result(columnNames, result, displayStart)


    while True:
        print("Avaliable actions:")
        print("1: Answer a question             5: next page")
        print("2: List answers of a question    6: previous page")
        print("3: Vote a question               7: refresh the page")
        print("4: Return")
        userInput = input(">>> ").strip()
        if not userInput.isdigit() or int(userInput) not in [1,2,3,4,5,6,7]:
            print("\nError: Invalid input\n")
        else:
            userInput = int(userInput)
            if userInput == 1:
                answer_question(client, db)
            
            

# The following functions are for multithreaded searh function implementation
def __convert_to_string(item):
    ''' convert dict to string '''
    return json.dumps(item, sort_keys=True)

def __convert_to_dict(item):
    ''' convert string to dict '''
    return json.loads(item)

DB = None
def initialize_db(db):
    ''' initialize db and collection for multithreading '''
    global DB
    DB = db

def search_thread(kw):
    ''' distribute search for each keyword '''
    kw = kw.strip()
    columns = ["Title", "Body", "Tags"]
    searchResult = set()
    findrgx = re.compile('.*' + re.escape(kw) + '.*', re.IGNORECASE)

    global DB
    collection_posts = DB["Posts"]

    with Pool(3) as p:
        result = list(p.map(partial(search_subthread, collection_posts, findrgx), columns))

    searchResult = set.union(*result)
    return searchResult

def search_subthread(collection_posts, findrgx, columnNames):
    ''' Search for each column '''
    result = collection_posts.find({"$and": [{"PostTypeId": "1", columnNames: findrgx}]})
    result = set(map(__convert_to_string, result))
    return result

def search_question(client, db, userID, keywords):
    ''' Search all matching questions given keywords '''
    print("Searching...")
    searchResult = list()
    initialize_db(db)
    # Remove duplicates
    keywords = list(set(keywords))
    if len(keywords) == 0:
        return None
    
    # spawn thread for every keyword for faster search
    with Pool(len(keywords)) as p:
        searchResult = list(p.map(search_thread, keywords))

    # remove duplicated result
    searchResult = set.union(*searchResult)

    # convert result to dict
    cpuava = multiprocessing.cpu_count()
    with Pool(cpuava) as p:
        returnResult = list(p.map(__convert_to_dict, searchResult))

    return returnResult

# end of search function


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
            if not result:
                print("\nNo result\n")
            else:
                question_actions(client, db, userID, result)

        elif int(userInput) == 3:
            # Quit
            print("\nReturning to Home Page")
            print("*-----------------------*")
            return
