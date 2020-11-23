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

def answer_question(client, db, searchResult, userID):
    ''' answer a question '''
    avaliable_posts = list(searchResult.keys())

    print("Enter Post ID to answer")
    userInput = input(">>> ").strip()
    if not userInput.isdigit() or int(userInput) not in avaliable_posts:
        print("Error: Invalid Post ID")
        return searchResult
    
    title, body = systemFunctions.editor()

    print("Please Review your post:")
    print("Title:")
    print(title)
    print("Body:")
    print(body)
    print()

    ans = input("Confirm Post? (y/N) ").strip()
    if ans not in ['y', 'Y', "yes", "Yes", "YES"]:
        print("Post Discarded")
        return

    print("Posting...")
    posts_row = dict()  # initialize row for storing entry
    collection_posts = db["Posts"]

    # Assign PID
    maxPID = collection_posts.find_one(sort=[("_id", -1)])["_id"] # First find the document containing the max Id, then extract its Id field
    assert type(maxPID) == int, "maxPID type error (maxPID = {})".format(maxPID)

    newId = maxPID + 1
    posts_row["_id"] = newId

    posts_row["PostTypeId"] = "2" # Post type = Answer
    posts_row["ParentId"] = str(userInput)
    posts_row["CreationDate"] = systemFunctions.get_currentTime()
    posts_row["Score"] = 0
    posts_row["Body"] = body
    if userID:
        posts_row["OwnerUserId"] = userID
    
    posts_row["Title"] = title

    # initialize comment count
    posts_row["CommentCount"] = 0

    # set content license
    posts_row["ContentLicense"] = "CC BY-SA 2.5"

    collection_posts.insert_one(posts_row)

    userInput = int(userInput)
    partentPost = collection_posts.find_one({"_id": userInput})

    try:
        anscount = int(partentPost["AnswerCount"])
        anscount += 1
        searchResult[userInput]["AnswerCount"] += 1
    except KeyError:
        anscount = 1
        searchResult[userInput]["AnswerCount"] = 1

    collection_posts.update_one({"_id": userInput}, {"$set": {"AnswerCount": anscount}})
    

    check = collection_posts.find_one({"_id": newId})
    if check:
        print("\nSuccess\n")
    else:
        print("\nDatabase Error: Posting Unsuccessful\n")

    return searchResult

def view_question(client, db, searchResult, userID):
    ''' View a specified question '''

    avaliable_posts = list(searchResult.keys())

    print("Enter Post ID to view")
    userInput = input(">>> ").strip()
    if not userInput.isdigit() or int(userInput) not in avaliable_posts:
        print("Error: Invalid Post ID")
        return searchResult, list()

    collection_posts = db["Posts"]
    userInput = int(userInput)
    questionPost = collection_posts.find_one({"_id": userInput})

    def __extract_title_body(post, answer=False):
        ''' extract the title and body of a post'''
        title = "None"
        body = "None"
        try:
            title = post["Title"]
            post.pop("Title", None)
        except KeyError:
            pass
        
        try:
            body = post["Body"]
            if answer:
                if len(body) > 80:
                    body = body[:80] + "..."
            post.pop("Body", None)
        except KeyError:
            pass
        return title, body

    # Get accepted answer, if any
    try:
        accans = questionPost["AcceptedAnswerId"]
        accans = int(accans)
        questionPost.pop("AcceptedAnswerId", None)
    except KeyError:
        accans = None

    # Get view count, if any
    try:
        viewCount = questionPost["ViewCount"] + 1
    except KeyError:
        viewCount = 1

    collection_posts.update_one({"_id": userInput}, {"$set": {"ViewCount": viewCount}})
    # print Question
    print("Viewing Question p/{}".format(userInput))
    title, body = __extract_title_body(questionPost)

    systemFunctions.print_text(title, body)
    print('-' * 90)
    for key, item in questionPost.items():
        key = str(key) + ":"
        print("{:<20} {}".format(key, item))
    print('=' * 90)
    print("** Answers:")
    avaliable_ans = list()
    # check and print accepted answer
    if accans:
        print("\n{:^90}\n".format("*** Accepted Answer ***"))
        accans = int(accans)
        avaliable_ans.append(accans)

        accepted_ans = collection_posts.find_one({"_id": accans})
        title, body = __extract_title_body(accepted_ans, answer=True)
        systemFunctions.print_text(title, body)
        print('- ' * 45)
        ans = accepted_ans

        content = ans["_id"]
        print("{:<20} {}".format("Post Id", content))
        
        try:
            content = ans["CreationDate"]
            print("{:<20} {}".format("Creation Date", content))
        except KeyError:
            pass

        try:
            content = ans["Score"]
            print("{:<20} {}".format("Score", content))
        except KeyError:
            print("{:<20} {}".format("Score", 0))

        print('='*90)
    
    parentID = str(userInput)
    answers = collection_posts.find({"PostTypeId": "2", "ParentId": parentID})
    for ans in answers:
        if int(ans["_id"]) == accans:
            continue    # accepted answer is already printed
        avaliable_ans.append(int(ans["_id"]))

        # print answers
        title, body = __extract_title_body(ans, answer=True)
        systemFunctions.print_text(title, body)
        print('- '*45)
        content = ans["_id"]
        print("{:<20} {}".format("Post Id", content))
        
        try:
            content = ans["CreationDate"]
            print("{:<20} {}".format("Creation Date", content))
        except KeyError:
            pass

        try:
            content = ans["Score"]
            print("{:<20} {}".format("Score", content))
        except KeyError:
            print("{:<20} {}".format("Score", 0))

        print('=' * 90)
    print()
    while True:
        print("Avaliable actions:")
        print("1. View details of an answer")
        print("2. Upvote an answer")
        print("3. Return to search result")
        userInput = input("(1/2/3) >>> ").strip()
        if not userInput.isdigit() or int(userInput) not in [1,2,3]:
            print("Error: Invalid Input")
        else:
            userInput = int(userInput)
            if userInput == 3:
                # Return to previous page
                return searchResult, avaliable_ans
            elif userInput == 1:
                # Detailed view of an answer

                PID = input("Enter Post Id >>> ").strip()
                if not PID.isdigit() or int(PID) not in avaliable_ans:
                    print("Error: Invalid Post Id")
                else:
                    PID = int(PID)
                    ans = collection_posts.find_one({"_id": PID})
                    print("\nViewing Answer p/{}".format(PID))
                    if PID == accans:
                        print("{:^90}".format("*** Accepted Answer ***"))
                    title, body = __extract_title_body(ans, answer=False)
                    systemFunctions.print_text(title, body)
                    print("- "*45)
                    for key, item in sorted(ans.items(), key=lambda x: x[0]):
                        key = str(key) + ':'
                        print("{:<20} {}".format(key, item))
                    print("="*90)
                    print()

            elif userInput == 2:
                # prompt to upvote
                searchResult = vote_post(client, db, searchResult, avaliable_ans, userID)


def vote_post(client, db, searchResult, avaliable_answers, userID):
    ''' upvote a question or answer '''
    # Prompt for user to input PID
    avaliable_posts = list(searchResult.keys())
    userInput = input("Enter Post Id >>> ").strip()
    if not userInput.isdigit() or (int(userInput) not in avaliable_posts and int(userInput) not in avaliable_answers):
        print("\nError: Invalid Post Id\n")
        return searchResult
    PID = int(userInput)

    collection_votes = db["Votes"]
    # check if user has already upvoted
    if userID:
        userID = str(userID)
        pid = str(PID)
        check = collection_votes.find_one({"UserId": userID, "PostId": pid})
        if check:
            print("\nError: Already voted\n")
            return searchResult

    collection_posts = db["Posts"]

    post = collection_posts.find_one({"_id": PID})
    try:
        votes = int(post["Score"])
        votes += 1
    except KeyError:
        votes = 1
    
    collection_posts.update_one({"_id": PID}, {"$set": {"Score": votes}})

    votes_row = dict()

    # assign VID
    maxVID = collection_votes.find_one(sort=[("_id", -1)])["_id"] # First find the document containing the max Id, then extract its Id field
    assert type(maxVID) == int, "maxPID type error (maxVID = {})".format(maxVID)

    newId = maxVID + 1
    votes_row["_id"] = newId
    votes_row["PostId"] = str(PID)
    votes_row["VoteTypeId"] = "2"
    if userID:
        votes_row["UserId"] = str(userID)
    votes_row["CreationDate"] = systemFunctions.get_currentTime()

    collection_votes.insert_one(votes_row)

    try:
        vt = searchResult[PID]["Score"]
        vt += 1
    except KeyError:
        vt = 1

    if PID in avaliable_posts:
        searchResult[PID]["Score"] = vt
    print("\nVote successful\n")
    return searchResult

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

    #result = sorted(result, key=lambda x: x[3], reverse=True)
    systemFunctions.display_result(columnNames, result, displayStart)

    avaliable_answers = list()

    while True:
        print("Avaliable actions:")
        print("1: Answer a question             4: Next page            7: Return")
        print("2: List answers of a question    5: Previous page")
        print("3: Vote a post                   6: Refresh result")
        userInput = input("(1/2/3/...) >>> ").strip()
        if not userInput.isdigit() or int(userInput) not in [1,2,3,4,5,6,7]:
            print("\nError: Invalid input\n")
        else:
            userInput = int(userInput)
            if userInput == 7:
                print()
                print("Welcome back")
                return
            elif userInput == 1:
                searchResult = answer_question(client, db, searchResult, userID)
            elif userInput == 2:
                searchResult, avaliable_answers = view_question(client, db, searchResult, userID)
            elif userInput == 3:
                searchResult = vote_post(client, db, searchResult, avaliable_answers, userID)
            elif userInput == 4:
                # Next page
                if (displayStart + 10) >= len(avaliable_posts):
                    print("Error: This is the last page")
                else:
                    displayStart += 10
                    systemFunctions.display_result(columnNames, result, displayStart)

            elif userInput == 5:
                # Prev page
                displayStart -= 10
                if displayStart < 0:
                    print("Error: This is the first page")
                    displayStart = 0
                else:
                    systemFunctions.display_result(columnNames, result, displayStart)

            elif userInput == 6:
                # Refresh display, assuming changes in searchResult
                result = [[key, item["Title"], item["CreationDate"], item["Score"], item["AnswerCount"]] for key, item in searchResult.items()]
                #result = sorted(result, key=lambda x: x[3], reverse=True)
                systemFunctions.display_result(columnNames, result, displayStart)

            else:
                print("Error: Invalid Input")

            

# The following functions are for multithreaded searh function implementation
def __convert_to_string(item):
    ''' convert dict to string '''
    return json.dumps(item, sort_keys=True)

def __convert_to_dict(item):
    ''' convert string to dict '''
    return json.loads(item)

DB = None
def __initialize_db(db):
    ''' initialize db for multithreading '''
    global DB
    DB = db

def __search_thread(kw):
    ''' distribute search for each keyword '''
    kw = kw.strip()
    columns = ["Title", "Body", "Tags"]
    searchResult = set()
    findrgx = re.compile('.*' + re.escape(kw) + '.*', re.IGNORECASE)

    global DB
    collection_posts = DB["Posts"]

    with Pool(3) as p:
        result = list(p.map(partial(__search_subthread, collection_posts, findrgx), columns))

    searchResult = set.union(*result)
    return searchResult

def __search_subthread(collection_posts, findrgx, columnNames):
    ''' Search for each column '''
    result = collection_posts.find({"$and": [{"PostTypeId": "1", columnNames: findrgx}]})

    with Pool(4) as p:
        result = set(p.map(__convert_to_string, result))

    return result

def search_question(client, db, userID, keywords):
    ''' Search all matching questions given keywords '''
    print("Searching...")
    searchResult = list()
    __initialize_db(db)
    # Remove duplicates
    keywords = list(set(keywords))
    if len(keywords) == 0:
        return None
    cpuava = multiprocessing.cpu_count()
    # spawn thread for every keyword for faster search
    with Pool(cpuava) as p:
        searchResult = list(p.map(__search_thread, keywords))

    # remove duplicated result
    searchResult = set.union(*searchResult)

    # convert result to dict
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
    posts_row["FavoriteCount"] = 0
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
