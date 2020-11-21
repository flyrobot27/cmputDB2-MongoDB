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
    
    title, body = systemFunctions.editor()


def session(client, db, userID=None):
    ''' User main page where they can post questions and search questions'''
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
