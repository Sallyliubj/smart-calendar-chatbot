import datetime as dt
import streamlit as st
from streamlit_calendar import calendar
from pymongo import MongoClient
import time
from datetime import timedelta
from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as ggi
import json

# MongoDB connection setup (using environment variables)
load_dotenv(".env")
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["smart_calendar_chatbot"]
collection = db["user_calendar"]
suggestion_collection = db["daily_suggestions"]

# Function to get user data from MongoDB by username
def get_user_data(username):
    user_data = collection.find_one({"username": username})
    if user_data:
        return user_data
    else:
        return None

# Helper function to convert weekday names to numbers
def get_weekday_number(day_name):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days.index(day_name)

# Generate a 60-minute time grid from 7 AM to 10 PM for a specific day
def generate_time_grid(start_time="07:00", end_time="22:00", interval_minutes=60):
    start = dt.datetime.strptime(start_time, "%H:%M").time()
    end = dt.datetime.strptime(end_time, "%H:%M").time()
    current = dt.datetime.combine(dt.date.today(), start)
    time_grid = []
    
    while current.time() <= end:
        time_grid.append(current.time())
        current += dt.timedelta(minutes=interval_minutes)
    
    return time_grid

# Mark time slots as occupied or free based on the class schedule
def mark_occupied_slots(time_grid, class_schedule, day_name):
    occupied_slots = set()
    for class_info in class_schedule:
        if class_info["day1"] == day_name or class_info["day2"] == day_name:
            class_start = dt.datetime.fromisoformat(class_info["start"]).time()
            class_end = dt.datetime.fromisoformat(class_info["end"]).time()
            
            # Mark slots as occupied if they overlap with the class schedule
            for slot in time_grid:
                if class_start <= slot < class_end:
                    occupied_slots.add(slot)
    
    return occupied_slots

# Find free time slots in the grid
def find_free_slots(time_grid, occupied_slots):
    free_slots = [slot for slot in time_grid if slot not in occupied_slots]
    return free_slots

# Suggest time slots for meals, exercise, and assignments
def suggest_time_slots(free_slots):
    suggestions = {
        "breakfast": None,
        "lunch": None,
        "dinner": None,
        "exercise": [],
        "assignments": []
    }
    
    # Suggest meal times
    for slot in free_slots:
        if dt.time(7, 0) <= slot <= dt.time(9, 0) and suggestions["breakfast"] is None:
            suggestions["breakfast"] = slot
        elif dt.time(12, 0) <= slot <= dt.time(14, 0) and suggestions["lunch"] is None:
            suggestions["lunch"] = slot
        elif dt.time(18, 0) <= slot <= dt.time(20, 0) and suggestions["dinner"] is None:
            suggestions["dinner"] = slot
        free_slots.remove(slot)
    
    # Suggest exercise times and assignment work in remaining free slots
    for slot in free_slots:
        if suggestions["breakfast"] and suggestions["lunch"] and suggestions["dinner"]:
            if dt.time(7, 0) <= slot <= dt.time(22, 0):
                suggestions["exercise"] = slot
                free_slots.remove(slot)
                break
    
    # Suggest time slots for assignments (remaining free time)
    suggestions["assignments"] = [slot for slot in free_slots]

    # Save suggestions to the JSON file
    save_suggestions_to_json(username, suggestions)
    
    return suggestions

# Define the JSON file path
suggestions_file = 'daily_suggestions.json'

# Function to save suggestions to a JSON file
def save_suggestions_to_json(username, suggestions):
    # Create a copy of suggestions for saving
    suggestions_to_save = suggestions.copy()
    
    # Convert time objects to strings in the copied dictionary
    for key in suggestions_to_save:
        if isinstance(suggestions_to_save[key], dt.time):
            suggestions_to_save[key] = suggestions_to_save[key].isoformat()  # Convert time to ISO format
        elif isinstance(suggestions_to_save[key], list):
            suggestions_to_save[key] = [slot.isoformat() if isinstance(slot, dt.time) else slot for slot in suggestions_to_save[key]]

    # Load existing suggestions from the file, if it exists
    if os.path.exists(suggestions_file):
        with open(suggestions_file, 'r') as f:
            all_suggestions = json.load(f)
    else:
        all_suggestions = {}

    # Add today's suggestions
    today = dt.datetime.now().date().isoformat()
    if username not in all_suggestions:
        all_suggestions[username] = {}

    all_suggestions[username][today] = suggestions_to_save

    # Write the updated suggestions back to the JSON file
    with open(suggestions_file, 'w') as f:
        json.dump(all_suggestions, f, indent=4)

# Helper function to generate recurring events until a specific end date
def generate_recurring_events(class_info, end_date):
    events = []
    
    # Parse the start and end times (same for all occurrences)
    start_time = dt.datetime.fromisoformat(class_info["start"]).time()
    end_time = dt.datetime.fromisoformat(class_info["end"]).time()
    
    # Parse the start date and first occurrence of day1 and day2
    start_date = dt.datetime.fromisoformat(class_info["start"]).date()
    
    day1 = get_weekday_number(class_info["day1"])
    day2 = get_weekday_number(class_info["day2"])
    
    current_date = start_date
    while current_date <= end_date:
        # Add class occurrences on day1 and day2
        if current_date.weekday() in [day1, day2]:
            start_dt = dt.datetime.combine(current_date, start_time)
            end_dt = dt.datetime.combine(current_date, end_time)
            events.append({
                "title": class_info["class"],
                "color": "#3DD56",  # Same color for all class events
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            })
        current_date += dt.timedelta(days=1)

    return events

# Helper function to add assignments to the event list
def generate_assignment_events(assignments):
    events = []
    for assignment in assignments:
        due_date = dt.datetime.strptime(assignment["due_date"], "%Y-%m-%d").date()
        events.append({
            "title": assignment["name"],
            "color": "#00FF00",  # Green color for assignments
            "start": due_date.isoformat(),
            "end": due_date.isoformat(),
            "allDay": True  # Mark assignment as all-day event
        })
    return events

# Main calendar visualizer function
def calendar_visualizer(username):
    # Fetch user data from MongoDB
    user_data = get_user_data(username)
    if not user_data:
        st.error(f"No data found for user: {username}")
        return

    st.markdown(f"## Weekly Calendar for {user_data['username']} 📆")
    
    # Define the end date for the week (7 days from today)
    end_date = dt.date.today() + dt.timedelta(days=7)
    
    # Prepare to store all events for the week
    events = []

    # Loop through each day of the week
    for i in range(7):
        current_day = dt.date.today() + dt.timedelta(days=i)
        day_name = current_day.strftime("%A")
        
        # Generate a time grid for the current day
        time_grid = generate_time_grid()
        
        # Mark occupied slots based on the user's class schedule
        occupied_slots = mark_occupied_slots(time_grid, user_data["class_schedule"], day_name)
        
        # Find the remaining free time slots
        free_slots = find_free_slots(time_grid, occupied_slots)
        
        # Suggest time slots for breakfast, lunch, dinner, exercise, and assignments
        suggestions = suggest_time_slots(free_slots)
        
        # Add suggested events to the weekly events list
        if suggestions["breakfast"]:
            start_time = dt.datetime.combine(current_day, suggestions["breakfast"])
            events.append({
                "title": "Breakfast",
                "color": "#FFA500",  # Orange color for meals
                "start": start_time.isoformat(),
                "end": (start_time + dt.timedelta(hours=1)).isoformat()            
            })

        if suggestions["lunch"]:
            start_time = dt.datetime.combine(current_day, suggestions["lunch"])
            events.append({
                "title": "Lunch",
                "color": "#FFA500",  # Orange color for meals
                "start": start_time.isoformat(),
                "end": (start_time + dt.timedelta(hours=1)).isoformat()   
            })

        if suggestions["dinner"]:
            start_time = dt.datetime.combine(current_day, suggestions["dinner"])
            events.append({
                "title": "Dinner",
                "color": "#FFA500",  # Orange color for meals
                "start": start_time.isoformat(),
                "end": (start_time + dt.timedelta(hours=1)).isoformat()   
            })

        if suggestions["exercise"]:
            start_time = dt.datetime.combine(current_day, suggestions["exercise"])
            events.append({
                "title": "Exercise",
                "color": "#FF6347",  # Tomato color for exercise
                "start": start_time.isoformat(),
                "end": (start_time + dt.timedelta(hours=1)).isoformat()   
            })

    # Generate recurring events for each class
    for class_info in user_data["class_schedule"]:
        recurring_events = generate_recurring_events(class_info, end_date)
        events.extend(recurring_events)

    # Generate assignment events
    assignment_events = generate_assignment_events(user_data["assignments"])
    events.extend(assignment_events)

    calendar_options = {
        "editable": True,
        "navLinks": True,
        "initialDate": dt.date.today().isoformat(),  # Set initial date to today
        "initialView": "listDay",    # Show a week view
    }

    state = calendar(
        events=st.session_state.get("events", events),
        options=calendar_options,
        key="week",
    )

    if state.get("eventsSet") is not None:
        st.session_state["events"] = state["eventsSet"]

def get_daily_suggestions():
    try:
        with open('daily_suggestions.json', 'r') as file:
            return json.load(file)  # Load and return the suggestions from the JSON file
    except FileNotFoundError:
        return {}  # Return an empty dictionary if the file is not found
    except json.JSONDecodeError:
        return {}  # Return an empty dictionary if the file is not valid JSON
    
# Function to check for upcoming events in the next hour
def check_for_upcoming_events(username):
    user_data = get_user_data(username)
    if not user_data:
        return "No data found"
    
    reminders = []
    
    # current_time = dt.datetime.now()
    current_time = dt.datetime(year=2024, month=10, day=6, hour=7, minute=0)

    for class_info in user_data["class_schedule"]:
        class_start = dt.datetime.fromisoformat(class_info["start"]).time()
        if current_time.time() <= class_start <= (current_time + dt.timedelta(hours=1)).time():
            reminders.append(f"Reminder: You have {class_info['class']} starting at {class_start}")
    
    for assignment in user_data["assignments"]:
        due_date = dt.datetime.strptime(assignment["due_date"], "%Y-%m-%d").date()
        if current_time.date() == due_date:
            reminders.append(f"Reminder: You have an assignment due today: {assignment['name']}")
        
    # Get daily suggestions from JSON
    suggestions = get_daily_suggestions()

    # Get today's date string
    current_date_str = current_time.strftime("%Y-%m-%d")
    
    # Check for suggestions for the user on today's date
    user_suggestions = suggestions.get(username, {}).get(current_date_str, {})
    
    # Check for meal and exercise suggestions
    for key, time_str in user_suggestions.items():
        if isinstance(time_str, str):  # Ensure the suggestion is a string
            try:
                suggestion_time = dt.datetime.strptime(time_str, "%H:%M:%S").time()  # Parse the time string
                # Combine today's date with the suggestion time
                full_suggestion_time = dt.datetime.combine(current_time.date(), suggestion_time)
                
                # Check if the current time is within the hour before the suggested time
                if full_suggestion_time == current_time:
                    reminders.append(f"Reminder: It's time for your suggested activity: {key} at {suggestion_time}")
            except ValueError:
                # Handle the case where the string is not in the correct format
                continue

    # Check for assignments suggestions
    assignments = user_suggestions.get("assignments", [])
    for assignment_time_str in assignments:
        if isinstance(assignment_time_str, str):
            try:
                assignment_time = dt.datetime.strptime(assignment_time_str, "%H:%M:%S").time()
                # Combine today's date with the assignment time
                full_assignment_time = dt.datetime.combine(current_time.date(), assignment_time)
                
                # Check if the current time is within the hour before the assignment time
                if full_assignment_time == current_time:
                    reminders.append(f"Reminder: It's time for your assignment at {assignment_time}")
            except ValueError:
                continue
    
    return reminders

def chatbot():
    # Load environment variables
    load_dotenv(".env")

    # Fetch API key from environment
    fetcheed_api_key = os.getenv("GOOGLE_API_KEY")

    # Configure Gemini API
    ggi.configure(api_key=fetcheed_api_key)

    # Set up the Gemini model
    model = ggi.GenerativeModel("gemini-pro") 
    chat = model.start_chat()

    # Function to handle responses from Gemini
    def LLM_Response(question):
        response = chat.send_message(question, stream=True)
        return response

    # Streamlit app
    st.markdown(f"## Chat with Your Personalized Assistant")

    # Input from user
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response from Gemini Pro
        with st.chat_message("assistant"):
            result = LLM_Response(prompt)
            for word in result:
                st.text(word.text)
        
        # Save the assistant's response to the session state
        st.session_state.messages.append({"role": "assistant", "content": ''.join([word.text for word in result])})


    # Reminder task to check for upcoming events
    while True:
        reminder_message = check_for_upcoming_events(username)  # Make sure username is defined
        if reminder_message:
            for message in reminder_message:
                st.session_state.messages.append({"role": "assistant", "content": message})
                with st.chat_message("assistant"):
                    st.markdown(message)
        
        time.sleep(3600)


# Call the function to display the calendar for the user
username = st.text_input("Enter username:", value="kusumaj")
if username:
    calendar_visualizer(username)

chatbot()