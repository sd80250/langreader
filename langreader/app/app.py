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

# initialization
corpus_length = corpus.get_corpus_length()
lower_bound = int(corpus_length*.25)
upper_bound = int(corpus_length*.75)
random_index = random.choice(range(lower_bound, upper_bound))

all_text_info = corpus.get_all_from_index(random_index)

text_title = all_text_info[1]
text_text = all_text_info[2]
text_url = corpus.find_gutenberg_url(all_text_info[3]) if all_text_info[10] == 'gutenberg' else all_text_info[3]
text_author = all_text_info[9]

session_state = session.get(username='', loggedIn = False, title_displaying=text_title, \
    text_displaying=text_text, author_displaying=text_author, url_displaying=text_url ,index=random_index, button_submitted=False)

def main():
    print('running 1')
    global session_state
    
    menu = ["Home", "Login", "Signup"]
    st.title("Reader App")

    print("running 2; logged in: {}".format(session_state.loggedIn))

    choice = st.sidebar.selectbox("Menu",menu)
    if choice == "Home":
        st.subheader("Home")
        if not session_state.loggedIn:
            st.info("You are currently not logged in. Head to the Login tab on the sidebar menu.")
    
    elif choice == "Login":
        if not session_state.loggedIn:
            login()
        else:
            st.sidebar.warning("You're already logged in! You looking to log out?")
            if st.sidebar.button("Log out"):
                reset()
    
    elif choice == "Signup":
        if not session_state.loggedIn:
            signup()


    if session_state.loggedIn == True:
        run_application()

# --username/password management--
def create_usertable():
    c1.execute('''        
    CREATE TABLE IF NOT EXISTS UsersTable(
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE, 
        password TEXT
    )''')

def add_userdata(username, password):
    c1.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn1.commit()

def login_user(username, password):
    c1.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username, password))
    data = c1.fetchall()
    return data

def view_all_users():
    c1.execute('SELECT * FROM userstable')
    data = c1.fetchall()
    return data
    
def reset():
    session_state.username = ''
    session_state.loggedIn = False

def signup():
    st.sidebar.subheader("Create New Account")
    new_user = st.sidebar.text_input("Username")
    new_pass = st.sidebar.text_input("Password", type = "password")

    if st.sidebar.button("Signup"):
        create_usertable()
        add_userdata(new_user, new_pass)
        st.sidebar.success("Successfully created a valid account")
        session_state.username = new_user
        session_state.loggedIn = True

def login():
    st.sidebar.subheader("Login")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type = "password")
    if st.sidebar.button("Login"):
        create_usertable()
        result = login_user(username, password)
        print("Result from login query: ", result)
        if result:
            session_state.username = username
            session_state.loggedIn = True
            #st.sidebar.success("Welcome, {}. Head back to the Home page.".format(session_state.username))
        else:
            st.sidebar.error("Error: Username/Password is incorrect")


# --helper methods--
def increment_index(difficulty):
    if difficulty == 'Too Easy':
        session_state.index += 5
    elif difficulty == 'Just Right':
        session_state.index += 2
    elif difficulty == 'Too Hard':
        session_state.index -= 3
    
    # won't work when new texts are added
    if session_state.index < 0:
        session_state.index = 0
        print('this is the first text in the corpus')
    
    if session_state.index > 99:
        session_state.index = 99
        print('this is the last text in the corpus')


def get_next_indices(difficulty, index):
    index_list = None
    if difficulty == 'Too Easy':
        interval = corpus_length//19
    elif difficulty == 'Just Right':
        interval = 2
    elif difficulty == 'Too Hard':
        interval = corpus_length//-31
    index_list = set(range(index + interval, index + interval*4, interval))

    # this won't work as new texts are added
    difference_set = set()
    for i in index_list:
        if i < 0 or i > corpus_length - 1:
            difference_set.add(i)

    index_list -= difference_set

    if len(index_list) == 0:
        if index < corpus_length/2:
            index_list = {0}
        else:
            index_list = {corpus_length - 1}

    return index_list


def set_session_state(all_from_index, indix):
    session_state.index = indix
    session_state.title_displaying = all_from_index[1]
    session_state.text_displaying = all_from_index[2]
    session_state.url_displaying = corpus.find_gutenberg_url(all_from_index[3]) if all_from_index[10] == 'gutenberg' else all_from_index[3]
    session_state.author_displaying = all_from_index[9]


#TODO: add functionality for adding a new text to corpus if the user wants to
def run_application():
    print("running 3; Printing because loggedIn is {0} and index is {1}".format(session_state.loggedIn, session_state.index))

    st.success("Welcome, {}!".format(session_state.username))
    
    st.write(session_state.index + 1, '/', corpus_length)
    st.progress(session_state.index / corpus_length)
    st.markdown("**Please read the text carefully.**")
    
    st.markdown("**_" + session_state.title_displaying.strip() + "_**")
    # st.write(f'<iframe src="https://www.gutenberg.org/files/398/398-h/398-h.htm#chap00" height="2400" width="800"></iframe>', unsafe_allow_html=True)
    print('author:', session_state.author_displaying)
    print('text:', True if session_state.text_displaying else False)
    print('url:', session_state.url_displaying)
    if session_state.author_displaying:
        st.markdown("*by " + session_state.author_displaying + "*")
    if session_state.text_displaying:
        if '\n' in session_state.text_displaying.strip():
            st.code(session_state.text_displaying, language="")
        else:
            st.write(session_state.text_displaying)
    elif session_state.url_displaying:
        st.write(f'<iframe src="' + session_state.url_displaying + '" height="900" width="800"></iframe>', unsafe_allow_html=True)

    with st.form('hi'):
        difficulty = st.select_slider(
            'How hard is this text for you?',
            options=['Too Easy', 'Just Right', 'Too Hard'])
        interest = st.select_slider(
            'How interesting is this text for you?',
            options=['Quite Boring', 'Somewhat Interesting', 'Very Interesting']
        )
        submit = st.form_submit_button('Get Another Text!')
    
    print('button_submitted:', session_state.button_submitted, "sumbit:", submit)
    if session_state.button_submitted or submit: #TODO: make sure user doesn't get the same text twice!
        print("running 4; button pressed")

        st.write('Here are some texts we thought would be appropriate:')

        next_indices = get_next_indices(difficulty, session_state.index)

        session_state.button_submitted = True # the button resets to False even if one of its children are pressed, so a persistent state is needed

        for column, indix in zip(st.beta_columns(len(next_indices)), next_indices):
            all_from_index = corpus.get_all_from_index(indix)

            with column:
                if st.button(all_from_index[1]): # displays the title
                    print('running 5; button pressed')
                    set_session_state(all_from_index, indix)
                    session_state.button_submitted = False
                    st.experimental_rerun()
        
        st.write('Here are the buttons for the easiest and hardest texts:')

        col1, col2 = st.beta_columns(2)
        with col1:
            all_from_index = corpus.get_all_from_index(0)

            if st.button(all_from_index[1], key=0):
                print('running 6; button pressed')
                set_session_state(all_from_index, 0)
                session_state.button_submitted = False
                st.experimental_rerun()
        
        with col2:
            all_from_index = corpus.get_all_from_index(corpus_length - 1)

            if st.button(all_from_index[1], key=1):
                print('running 6; button pressed')
                set_session_state(all_from_index, corpus_length - 1)
                session_state.button_submitted = False
                st.experimental_rerun()
    else: # if the button hasn't been pressed
        st.info("**Too Easy**: I understand the message, and I can read the text very fluently.\n\n \
**Just Right**: I understand the message, but there are some words I don't understand.\n\n \
**Too Hard**: I don't understand the message.")
        st.info("**Quite Boring**: I would rather do anything than read a similar text.\n\n \
**Somewhat Interesting**: I could keep reading something similar if I was asked to.\n\n \
**Very Interesting**: I want to read a similar text right now!")        


if __name__ == '__main__':
    main()

