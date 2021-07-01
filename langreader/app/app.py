import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import session
import sqlite3
import random
import corpus

# DB Management
conn1 = sqlite3.connect("resources/sqlite/corpus.sqlite")
c1 = conn1.cursor()

# session state
ss = session.get(username=None, loggedIn=False, index=None, button_submitted=False, done_setting_up=False, 
    corpus_length=None, order_strings=None, text_type=None,
    params=None) # TODO: add a language variable


def set_ss(indix):
    ss.index = indix
    ss.params = corpus.get_all(ss.text_type, ss.order_strings[indix])


def set_text_type(text_type):
    if ss.text_type != text_type:
        ss.text_type = text_type
        ss.corpus_length = corpus.get_corpus_length(ss.text_type)
        ss.order_strings = corpus.get_order_strings(ss.text_type)
        ss.index = None
        ss.params = None


# initialization
def initialization():
    if not ss.index:
        last_index = get_last(ss.text_type)
        if not last_index and last_index != 0:
            ss.corpus_length = corpus.get_corpus_length(ss.text_type)
            ss.order_strings = corpus.get_order_strings(ss.text_type)

            lower_bound = int(ss.corpus_length*.25)
            upper_bound = int(ss.corpus_length*.75)
            last_index = random.choice(range(lower_bound, upper_bound))

        set_ss(last_index)

def main():
    global ss
    st.title("Reader App Demo")

    if not ss.loggedIn:
        menu = ["Home", "Login", "Signup"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Home":
            st.subheader("Home")
            st.info("You are currently not logged in. Head to the Login tab on the sidebar menu.")
        
        elif choice == "Login":
            login()
        
        elif choice == "Signup":
            signup()
        
    else:
        menu = ["Poems", "Short Stories", "Sign Out"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Poems":
            set_text_type('poem')
        elif choice == "Short Stories":
            set_text_type("short_story")
        elif choice == "News":
            set_text_type("news")
        elif choice == "Sign Out":
            if st.sidebar.button("Log out"):
                reset()
        
        initialization()

        run_application()

# --username/password management--
def create_usertable():
    c1.execute('''        
    CREATE TABLE IF NOT EXISTS UsersTable(
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE, 
        password TEXT,
        last_poem_id INTEGER,
        last_short_story_id INTEGER,
        last_news_id INTEGER
    );''')

def add_userdata(username, password): # returns whether sign up was successful
    c1.execute('SELECT * FROM UsersTable WHERE username = ?', (username,))
    if c1.fetchall():
        return False
    c1.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn1.commit()
    return True

def login_user(username, password):
    c1.execute('SELECT * FROM userstable WHERE username = ? AND password = ?', (username, password))
    data = c1.fetchall()
    return data

def view_all_users():
    c1.execute('SELECT * FROM userstable')
    data = c1.fetchall()
    return data

def get_column_name(text_type):
    column_name = None
    if text_type == "poem":
        column_name = "last_poem_id"
    elif text_type == "short_story":
        column_name = 'last_short_story_id'
    elif text_type == "news":
        column_name = 'last_news_id'
    return column_name

def get_last(text_type):
    c1.execute('SELECT ' + get_column_name(text_type) + ' FROM UsersTable WHERE username = ?', (ss.username,))
    return c1.fetchone()[0]

def set_last(text_type):
    c1.execute('UPDATE UsersTable SET ' + get_column_name(text_type) + ' = ' + str(ss.index) + ' WHERE username = ?', (ss.username,))
    conn1.commit()
    
def reset():
    ss.username = None 
    ss.loggedIn = False
    ss.index = None
    ss.button_submitted = False
    ss.done_setting_up = False
    ss.corpus_length = None
    ss.order_strings = None
    ss.text_type = None
    ss.params = None
    st.experimental_rerun()

def signup():
    st.sidebar.subheader("Create New Account")
    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type = "password")

    if st.sidebar.button("Signup"):
        create_usertable()
        if add_userdata(new_user, new_pass):
            st.sidebar.success("Successfully created a valid account")
            ss.username = new_user
            ss.loggedIn = True
            st.experimental_rerun()
        else:
            st.sidebar.error("Username already taken")

def login():
    st.sidebar.subheader("Login")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type = "password")
    if st.sidebar.button("Login"):
        create_usertable()
        result = login_user(username, password)
        print("Result from login query: ", result)
        if result:
            ss.username = username
            ss.loggedIn = True
            st.experimental_rerun()
            #st.sidebar.success("Welcome, {}. Head back to the Home page.".format(ss.username))
        else:
            st.sidebar.error("Error: Username/Password is incorrect")

# --record readability/enjoyability of text--
def record_difficulty_and_interest(difficulty, interest, username, language, text_type, order_string):
    c1.execute('SELECT user_id FROM UsersTable WHERE username = ?', (username, ))
    user_id = c1.fetchone()[0]
    c1.execute('SELECT article_id FROM Repository WHERE language = ? AND text_type = ? AND order_string = ?', (language, text_type, order_string))
    article_id = c1.fetchone()[0]

    difficulty_int = 1 if difficulty == 'Too Easy' else 2 if difficulty == 'Just Right' else 3 if difficulty == 'Too Hard' else -1
    interest_int = 1 if interest == 'Very Boring' else 2 if interest == 'Somewhat Interesting' else 3 if interest == 'Very Interesting' else -1
    
    c1.execute('INSERT OR REPLACE INTO UserRatings VALUES (null, ?, ?, ?, ?)', (user_id, article_id, difficulty_int, interest_int))
    conn1.commit()


# --helper methods--
def get_next_indices(difficulty, index):
    index_list = None
    if difficulty == 'Too Easy':
        interval = ss.corpus_length//19
    elif difficulty == 'Just Right':
        interval = 2
    elif difficulty == 'Too Hard':
        interval = ss.corpus_length//-31
    index_list = set(range(index + interval, index + interval*4, interval))

    # this won't work as new texts are added
    difference_set = set()
    for i in index_list:
        if i < 0 or i > ss.corpus_length - 1:
            difference_set.add(i)

    index_list -= difference_set

    if len(index_list) == 0:
        if index < ss.corpus_length/2:
            index_list = {0}
        else:
            index_list = {ss.corpus_length - 1}

    return index_list



#TODO: add functionality for adding a new text to corpus if the user wants to
def run_application():
    print("running 3; Printing because loggedIn is {0} and index is {1}".format(ss.loggedIn, ss.index))
    set_last(ss.text_type)
    st.success("Welcome, {}!".format(ss.username))
    
    st.write(ss.index + 1, '/', ss.corpus_length)
    st.progress(ss.index / ss.corpus_length)
    st.markdown("**Please read the text carefully.**")
    
    st.markdown("**_" + ss.params[1].strip() + "_**") # 1 > article_title
    print('author:', ss.params[9]) # 9 > article_author
    print('text:', True if ss.params[2] else False) # 2 > article_text
    print('url:', ss.params[3]) # 3 > article_url
    if ss.params[9]: # 9 > article_author
        st.markdown("*by " + ss.params[9] + "*")
    if not ss.params[2]: # 2 > article_text
        st.write(f'<iframe src="' + ss.params[3] + '" height="900" width="800"></iframe>', unsafe_allow_html=True)
    else:
        if ss.params[3]: # 3 > article_url
            st.write(ss.params[3])
        # if '\n' in ss.params[2].strip():
        #     st.code(ss.params[2], language="")
        # else:
        #     st.write(ss.params[2])
        st.write(ss.params[2])

    with st.form('hi'):
        difficulty = st.select_slider(
            'How hard is this text for you?',
            options=['Too Easy', 'Just Right', 'Too Hard'])
        interest = st.select_slider(
            'How interesting is this text for you?',
            options=['Very Boring', 'Somewhat Interesting', 'Very Interesting']
        )
        submit = st.form_submit_button('Get Another Text!')
    
    print('button_submitted:', ss.button_submitted, "sumbit:", submit)
    if ss.button_submitted or submit: #TODO: make sure user doesn't get the same text twice!
        print("running 4; button pressed")

        record_difficulty_and_interest(difficulty, interest, ss.username, 'english', ss.text_type,  ss.order_strings[ss.index])

        st.write('Here are some texts we thought would be appropriate:')

        next_indices = get_next_indices(difficulty, ss.index)

        ss.button_submitted = True # the button resets to False even if one of its children are pressed, so a persistent state is needed

        for column, indix in zip(st.beta_columns(len(next_indices)), next_indices):
            title = corpus.get_all(ss.text_type, ss.order_strings[indix])[1] # 1 > title

            with column:
                if st.button(title): 
                    print('running 5; button pressed')
                    set_ss(indix)
                    ss.button_submitted = False
                    st.experimental_rerun()
        

        with st.form('explicit_number'):
            explicit_index = st.number_input('Or, go enter an index from 0 to ' + str(ss.corpus_length - 1) + ' to go to a custom text.', min_value=0, max_value=ss.corpus_length-1)
            num_submit = st.form_submit_button()
        if num_submit:
            print('running 5; button pressed')
            set_ss(explicit_index)
            ss.button_submitted = False
            st.experimental_rerun()


#     else: # if the button hasn't been pressed
#         st.info("**Too Easy**: I understand the message, and I can read the text very fluently.\n\n \
# **Just Right**: I understand the message, but there are some words I don't understand.\n\n \
# **Too Hard**: I don't understand the message.")
#         st.info("**Quite Boring**: I would rather do anything than read a similar text.\n\n \
# **Somewhat Interesting**: I could keep reading something similar if I was asked to.\n\n \
# **Very Interesting**: I want to read a similar text right now!")        


if __name__ == '__main__':
    main()

