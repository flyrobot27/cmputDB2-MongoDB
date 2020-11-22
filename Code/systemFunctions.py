try:
    import curses
    import curses.textpad
    from datetime import datetime
except ImportError as e:
    print("Error: Compulsory package missing:",e)
    print("Please ensure requirements are satisfied.")
    exit(1)

def editor(pretitle="", prebody=""):
    '''
    A simple editor for posting questions or answers. Returns the title and body of the post
    It can also edit post given the title and body of the post wanted to be modified
    '''

    # initialize command line text editor with curses
    stdscr = curses.initscr()
    curses.noecho()      # displaying keys only when required
    curses.cbreak()      # no Enter key required
    stdscr.keypad(True)  # enable special keys

    begin_x = 0         # starting x coordinate
    begin_y = 0         # starting y coordinate
    # rows, cols = stdscr.getmaxyx()   # get display dimention of the console # This is causing issues with the lab machines
    rows, cols = 15, 55

    win = curses.newwin(rows, cols, begin_y, begin_x)   # create window
    win.addstr(begin_y, begin_x, "Edit your post here. Press Ctrl + G to switch and exit.")
    win.addstr(begin_y + 1, begin_x, "Title:")
    win.addstr(begin_y + 3, begin_x, "Body:")
    win.addstr(rows - 3, begin_x, "-" * cols)
    win.refresh()

    # initialize subwindow
    titlewin = win.subwin(1, cols ,begin_y + 2, begin_x)
    titlewin.addstr(0, 0, pretitle) # if a previous post title is supplied load the previous post

    bodywin = win.subwin(rows - 7, cols ,begin_y + 4, begin_x)
    bodywin.addstr(0, 0, prebody) # load previous post body

    # refresh previous text
    bodywin.refresh()
    titlewin.refresh()

    replywin = win.subwin(1, 5, rows - 2, begin_x + 22)
    redisplay = win.subwin(1, 22, rows - 2, begin_x)

    while True:
        title = curses.textpad.Textbox(titlewin, insert_mode=True).edit()
        bodywin.refresh() # refresh to update cursor location
        body = curses.textpad.Textbox(bodywin, insert_mode=True).edit()

        redisplay.addstr(0, 0, "Exit and save? (y/N) ")
        redisplay.refresh()

        reply = curses.textpad.Textbox(replywin, insert_mode=True).edit(lambda x: 7 if x == 10 else x)  # convert Ctrl+G to Enter

        if reply.strip() in ['y', 'Y', "yes", "Yes", "YES"]:
            break
        else:  # return to edit post
            redisplay.clear()
            redisplay.refresh()
            replywin.clear()
            replywin.refresh()

    # restore configuration
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()

    return title, body

def get_currentTime():
    ''' Return current date + time in the required format '''
    date = str(datetime.now())
    date = date[:10] + 'T' +date[11:23]
    return date

def display_result(columnNames, result, displayStart):
    '''
    Display results in a command line table
    columnNames and results will be tuple of strings or integer
    It will only display at most 10 results
    '''
    resultLength = len(result)

    displayEnd = displayStart + 10  # at most 5 results per page
    if displayEnd >= resultLength: # prevent integer overflow
        displayEnd = resultLength

    displayResult = result[displayStart:displayEnd]

    # Format result to ensure they do not exceed specific length
    for text in displayResult:
        # remove newline and tab
        title = text[1]
        title = title.replace("\n",'').replace("\t",'')
        if len(title) > 50:
            title = title[:47]
            title += "..."
        text[1] = title
        
    print()
    print('='*111)
    print("{:<9}  {:<50}  {:<25}  {:>7}  {:>11}".format(*columnNames))
    print("-"*9+"  "+"-"*50+"  "+"-"*25+"  "+"-"*7+"  "+"-"*11) 
    for text in displayResult:
        print("{:<9}  {:<50}  {:<25}  {:>7}  {:>11}".format(*text))
    print('='*111)
    print("Displaying Result ({0}-{1})/{2}".format(str(displayStart + 1), displayEnd, resultLength))
    print()
    return

def print_report(client, db, userID):
    ''' Print user report given a userID '''

    assert type(userID) == str, 'input type incorrect'

    collection_posts = db["Posts"]

    reportStr = ''
    print("\nGenerating User Report...")

    reportStr += "\n*** Report for u/" + userID + ": ***\n\n"

    # Find question count and average score for user
    questions = collection_posts.find({"OwnerUserId": userID, "PostTypeId": "1"})
    if questions.count() == 0:
        reportStr += "No questions have been posted by u/{}.\n\n".format(userID)
    else:
        reportStr += "Question(s) Posted:  {}\n".format(questions.count())
        total_score = [q["Score"] for q in questions]
        avg = sum(total_score) / (questions.count())
        reportStr += "Average Score:       {:.1f}\n\n".format(avg)

    # Find answer count and average score for user
    answers = collection_posts.find({"OwnerUserId": userID, "PostTypeId": "2"})
    if answers.count() == 0:
        reportStr += "No answers have been posted by u/{}.\n\n".format(userID)
    else:
        reportStr += "Answer(s) Posted:    {}\n".format(answers.count())
        total_score = [a["Score"] for a in answers]
        avg = sum(total_score) / (answers.count())
        reportStr += "Average Score:       {:.1f}\n\n".format(avg)

    collection_votes = db["Votes"]
    userVotes = collection_votes.find({"UserId": userID})
    reportStr += "Votes Casted:        {}\n".format(userVotes.count())
    reportStr += "\n*** END OF REPORT ***\n"
    print(reportStr)
    _ = input("Press Enter to continue ")
    print()

def print_text(title, body):
    '''
    A simple function to print the title and body
    Imported from project 1
    '''

    def _parse(text):
        '''
        Parse the given text to the length 90
        '''

        newtext = list(text)
        accu = 0
        i = 0
        while i < len(text):
            if newtext[i] == '\n':
                accu = 0
                i += 1
            else:
                if accu > 88:
                    if newtext[i] == " ":
                        newtext.insert(i+1, '\n')
                    elif newtext[i - 1] == " ":
                        newtext.insert(i, '\n')
                    else:
                        newtext.insert(i, "-\n")

                    accu = 0
                else:
                    accu += 1
                
                i += 1

        return ''.join(newtext)

    print("-" * 90)
    if len(title) < 83:
        print("Title:",title)
    else:
        newtitle = _parse(title)
        print("Title:")
        print(newtitle)

    print("- " * 45)

    if len(body) < 83:
        print(body)
    else:
        newbody = _parse(body)
        print()
        print(newbody)