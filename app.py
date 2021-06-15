import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
import session
import sqlite3

# DB Management
conn = sqlite3.connect("data.db")
c = conn.cursor()

def main():
    global session_state

    session_state = session.get(username='', loggedIn = False)

    menu = ["Home", "Login", "Signup"]
    st.title("Reader App")

    print("logged in: {}".format(session_state.loggedIn))

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
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')

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

def run_application():
    st.success("Welcome, {}".format(session_state.username))
    print("Printing because loggedIn is {}".format(session_state.loggedIn))
    story = st.text_area("Enter Text: ")
    difficulty = st.select_slider(
        'Select the level of difficulty of this text for you',
        options=['Too Easy', 'Just Right', 'Too Hard'])
    st.write('Difficulty selected: ', difficulty)


    if story != "":
        st.write('''Contrary to popular belief, Lorem Ipsum is not simply random text. It has roots in a piece of classical Latin literature from 45 BC, making it over 2000 years old. Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going through the cites of the word in classical literature, discovered the undoubtable source. Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of "de Finibus Bonorum et Malorum" (The Extremes of Good and Evil) by Cicero, written in 45 BC. This book is a treatise on the theory of ethics, very popular during the Renaissance. The first line of Lorem Ipsum, "Lorem ipsum dolor sit amet..", comes from a line in section 1.10.32.''')


if __name__ == '__main__':
    main()

