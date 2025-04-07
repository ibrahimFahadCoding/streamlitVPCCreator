import streamlit as st
import json
import os

# Set up the page title
st.set_page_config(page_title="Create User", layout="centered")

# Path to the users.json file
USER_FILE = "users.json"

# Check if users file exists and load it, otherwise initialize empty
if os.path.exists(USER_FILE):
    with open(USER_FILE, "r") as file:
        users = json.load(file)
else:
    users = {}

# Function to save new user to users.json
def save_user(username, password):
    users[username] = password
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)

# Title and instructions
st.title("🧑‍💻 Create New User")

# Create user form
with st.form("create_user_form"):
    st.subheader("Create a New User")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    create_user_button = st.form_submit_button("Create User")

# Handle form submission
if create_user_button:
    if not new_username or not new_password:
        st.warning("Please enter both username and password.")
    elif new_username in users:
        st.warning("This username already exists. Please choose another one.")
    else:
        # Save the new user
        save_user(new_username, new_password)
        st.success(f"✅ User `{new_username}` created successfully!")
