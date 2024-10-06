import streamlit as st
import pymongo
from pymongo import MongoClient
import bcrypt
from icalendar import Calendar
import datetime
import pandas as pd
from datetime import timedelta
import pytz

import os

# Step 1: Connect to MongoDB
client = MongoClient("mongodb+srv://kusumajaipiam:UCzCvw1d9nuIh7qU@cluster0.fk3ak.mongodb.net/?authMechanism=SCRAM-SHA-1")
db = client["smart_calendar_chatbot"]
users_collection = db["user_profiles"]

# Set OpenAI API key
#gemini.api_key = os.getenv("AIzaSyCYHFCUF7vSt6ZZNbJ1S4mBSBWSsLgG1dE")

# Step 2: Streamlit Interface for User Registration and Login
st.title("User Registration and Login")

# Choose between registration and login
choice = st.sidebar.selectbox("Choose Action", ["Register", "Login"])
st.session_state.choice = choice

# Step 3: User Registration

if choice == "Register":
    st.subheader("Create a New Account")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    sleep_habit = st.radio("Are you an early bird or a night owl?", ("Early Bird", "Night Owl"))
    sports_interest = st.multiselect("What sports do you like?", ["Gym", "Tennis", "Badminton", "Hiking", "Swimming", "Running"])
    exercise_frequency = {}
    for sport in sports_interest:
        frequency = st.selectbox(f"How often do you want to do {sport} per week?", ["Less than 1", 1, 2, 3, 4, 5, 6, 7], key=f"exercise_{sport}")
        exercise_frequency[sport] = frequency
    dietary_preference = st.selectbox("What are your dietary preferences?", ["Salad", "Fast Food", "Vegetarian", "Vegan", "Balanced Diet", "Keto"])
    

    # Optional calendar upload
    st.subheader("Upload Your Calendar (Optional)")
    uploaded_file = st.file_uploader("Upload your .ics calendar file", type="ics")
    calendar_events = []
    if uploaded_file is not None:
        gcal = Calendar.from_ical(uploaded_file.read())
        for component in gcal.walk():
            if component.name == "VEVENT":
                event_name = component.get('summary')
                event_begin = component.get('dtstart').dt
                if isinstance(event_begin, (datetime.datetime, datetime.date)):
                    event_begin = event_begin.isoformat()
                calendar_events.append({"name": event_name, "begin": event_begin})

    # Ask about weekly assignments
    st.subheader("Weekly Assignments")
    assignments = []
    num_assignments = st.number_input("How many assignments do you have this week?", min_value=0, step=1)
    for i in range(int(num_assignments)):
        assignment_name = st.text_input(f"Assignment {i + 1} name:", key=f"assignment_name_{i}")
        due_date = st.date_input(f"Assignment {i + 1} due date:", key=f"due_date_{i}")
        assignments.append({"assignment_name": assignment_name, "due_date": due_date.isoformat()})
    

    if st.button("Register", key="register_button"):
        if password != confirm_password:
            st.error("Passwords do not match. Please try again.")
        else:
            # Hash the password before storing it
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Insert user data into MongoDB
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "sleep_habit": sleep_habit,
                "sports_interest": sports_interest,
                "dietary_preference": dietary_preference,
                "exercise_frequency": exercise_frequency,
                "calendar_events": calendar_events,
                "assignments": assignments
            }
            users_collection.insert_one(user_data)

            st.success("Account created successfully! Please log in.")
            st.session_state.choice = "Login"



# Step 4: User Login
if choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        # Find user in MongoDB
        user = users_collection.find_one({"username": username})
        
        if user:
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                st.success(f"Welcome back, {username}!")
                st.session_state.user = user
            else:
                st.error("Incorrect password. Please try again.")
        else:
            st.error("Username not found. Please register first.")
                
if "user" in st.session_state:
    user = st.session_state.user
              
    # Display additional user information
    st.write("### Your Information:")
    st.write(f"**Email**: {user['email']}")
    st.write(f"**Sleep Habit**: {user['sleep_habit']}")
    st.write(f"**Sports Interest**: {user['sports_interest'] if isinstance(user['sports_interest'], str) else ', '.join(user['sports_interest'])}")
    st.write(f"**Dietary Preference**: {user['dietary_preference']}")
    st.write("**Exercise Frequency:**")
    if isinstance(user['exercise_frequency'], dict):
        for sport, frequency in user['exercise_frequency'].items():
            st.write(f"- {sport}: {frequency} times per week")
    else:
        st.write("- No exercise frequency data available")

    # Display calendar events for the upcoming week if available
    if "calendar_events" in user and user["calendar_events"]:
        st.write("### Your Calendar Events for the Upcoming Week:")
        calendar_df = pd.DataFrame(user["calendar_events"])
        calendar_df["begin"] = pd.to_datetime(calendar_df["begin"], errors='coerce')
        today = datetime.datetime.now(pytz.utc)
        next_week = today + timedelta(weeks=1)
        upcoming_events = calendar_df[(calendar_df["begin"] >= today) & (calendar_df["begin"] <= next_week)]
        for _, event in upcoming_events.iterrows():
            st.write(f"- {event['name']} on {event['begin']}")

    # Display assignments if available
    if "assignments" in user and user["assignments"]:
        st.write("### Your Weekly Assignments:")
        for assignment in user["assignments"]:
            st.write(f"- {assignment['assignment_name']} due on {assignment['due_date']}")
    

    # Ask user if they want to modify data
    modify_choice = st.radio("Do you want to modify your information or upload more data?", ("No", "Yes"))
    if modify_choice == "Yes":
        # Allow user to modify their data
        st.subheader("Modify Your Information")
        new_username = st.text_input("Username", value=user["username"], key="modify_username")
        new_email = st.text_input("Email", value=user["email"], key="modify_email")
        new_sleep_habit = st.radio("Are you an early bird or a night owl?", ("Early Bird", "Night Owl"), index=(0 if user["sleep_habit"] == "Early Bird" else 1), key="modify_sleep_habit")
        new_sports_interest = st.multiselect("What sports do you like?", ["Gym", "Tennis", "Badminton", "Hiking", "Swimming", "Running"], default=user["sports_interest"], key="modify_sports_interest")
        new_exercise_frequency = {}
        for sport in new_sports_interest:
            new_frequency = st.selectbox(f"How often do you want to do {sport} per week?", ["Less than 1", 1, 2, 3, 4, 5, 6, 7], key=f"modify_exercise_{sport}")
            new_exercise_frequency[sport] = new_frequency
        new_dietary_preference = st.selectbox("What are your dietary preferences?",
                                              ["Salad", "Fast Food", "Vegetarian", "Vegan", "Balanced Diet", "Keto"],
                                            index=["Salad", "Fast Food", "Vegetarian", "Vegan", "Balanced Diet", "Keto"].index(user["dietary_preference"]), key="modify_dietary_preference")
        
        
        # Optional calendar upload
        st.subheader("Upload a New Academic Calendar (Optional)")
        new_uploaded_file = st.file_uploader("Upload your .ics calendar file", type="ics", key="modify_calendar")
        new_calendar_events = []
        if new_uploaded_file is not None:
            gcal = Calendar.from_ical(new_uploaded_file.read())
            for component in gcal.walk():
                if component.name == "VEVENT":
                    event_name = component.get('summary')
                    event_begin = component.get('dtstart').dt
                    if isinstance(event_begin, (datetime.datetime, datetime.date)):
                        event_begin = event_begin.isoformat()
                    new_calendar_events.append({"name": event_name, "begin": event_begin})
        else:
            new_calendar_events = user.get("calendar_events", [])


        # Modify Weekly Assignments
        st.subheader("Modify Weekly Assignments")
        new_assignments = []
        num_assignments = st.number_input("How many assignments do you have this week?", min_value=0, step=1, value=len(user.get("assignments", [])), key="modify_num_assignments")

        for i in range(int(num_assignments)):
            assignment_data = user.get("assignments", [])
            assignment_name = st.text_input(f"Assignment {i + 1} name:", value=assignment_data[i]["assignment_name"] if i < len(assignment_data) else "", key=f"modify_assignment_name_{i}")
            
            # Convert the due date to datetime.date format
            due_date_str = assignment_data[i]["due_date"] if i < len(assignment_data) else datetime.date.today().isoformat()
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date() if isinstance(due_date_str, str) else due_date_str
            
            due_date = st.date_input(f"Assignment {i + 1} due date:", value=due_date, key=f"modify_due_date_{i}")
            new_assignments.append({"assignment_name": assignment_name, "due_date": due_date.isoformat()})
            
        # Save modifications
        if st.button("Save Modifications", key="save_modifications"):
            users_collection.update_one(
                {"username": new_username},
                {"$set": {
                    "username": new_username,
                    "email": new_email,
                    "sleep_habit": new_sleep_habit,
                    "sports_interest": new_sports_interest,
                    "dietary_preference": new_dietary_preference,
                    "exercise_frequency": new_exercise_frequency,
                    "calendar_events": new_calendar_events,
                    "assignments": new_assignments
                }}
            )
            st.success("Your information has been updated!")
            st.session_state.user = users_collection.find_one({"username": new_username})
            #st.experimental_rerun()

    
    # Link to External Resource for Generating Personalized Calendar
    if True:
        st.write("### Generating Personalized Calendar")
        st.write("Click the link below to generate your personalized weekly schedule using the chatbot.")
        button_html = '<a href="http://10.207.36.19:8501" target="_blank"><button>Generate Personalized Calendar</button></a>'
        st.markdown(button_html, unsafe_allow_html=True)