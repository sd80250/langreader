import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import session
import sqlite3
import random

# DB Management
conn = sqlite3.connect("corpus.sqlite")
c = conn.cursor()

def main():
    print('running 1')
    global session_state

    order_strings = get_order_strings()
    lower_bound = int(len(order_strings)*.25)
    upper_bound = int(len(order_strings)*.75)
    random_index = random.choice(range(lower_bound, upper_bound))

    session_state = session.get(username='', loggedIn = False, text_displaying = get_text(order_strings[random_index]), order_strings = order_strings, index = random_index)

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

def create_usertable():
    c.execute('''        
    CREATE TABLE IF NOT EXISTS UsersTable(
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE, 
        password TEXT
    )''')

def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username, password))
    data = c.fetchall()
    return data

def view_all_users():
    c.execute('SELECT * FROM userstable')
    data = c.fetchall()
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

def get_text(text_order_index):
    c.execute('SELECT article_text FROM Repository WHERE order_string = ?', (text_order_index))
    return c.fetchone()[0]

def get_order_strings():
    c.execute('SELECT order_string FROM Repository ORDER BY order_string')
    return c.fetchall()

def increment_index(difficulty):
    if difficulty == 'Too Easy':
        session_state.index += 5
    elif difficulty == 'Just Right':
        session_state.index += 2
    elif difficulty == 'Too Hard':
        session_state.index -= 3
    
    if session_state.index < 0:
        session_state.index = 0
        print('this is the first text in the corpus')
    
    if session_state.index > 99:
        session_state.index = 99
        print('this is the last text in the corpus')

#TODO: add functionality for adding a new text to corpus if the user wants to
def run_application():
    print("running 3; Printing because loggedIn is {0} and index is {1}".format(session_state.loggedIn, session_state.index))

    st.success("Welcome, {}".format(session_state.username))

    st.progress(session_state.index)
    st.markdown("**Please read the text carefully.**")
    st.code("\n\n" + session_state.text_displaying, language=None)

    difficulty = st.select_slider(
        'How hard is this text for you?',
        options=['Too Easy', 'Just Right', 'Too Hard'])
    st.write('Difficulty: ' + difficulty)
    #TODO: present user with three texts and allow them to choose afterwards (or something similar)
    if st.button('Get Another Text!'): #TODO: make sure user doesn't get the same text twice!
        print("running 4; button pressed")
        increment_index(difficulty)
        session_state.text_displaying = get_text(session_state.order_strings[session_state.index])
        st.experimental_rerun()
if __name__ == '__main__':
    main()

