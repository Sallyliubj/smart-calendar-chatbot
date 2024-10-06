from streamlit_calendar import calendar
import datetime as dt
import streamlit as st
from pymongo import MongoClient
from collections import defaultdict


# MongoDB connection setup (update with your credentials)
client = MongoClient("mongodb+srv://kusumajaipiam:UCzCvw1d9nuIh7qU@cluster0.fk3ak.mongodb.net/?authMechanism=SCRAM-SHA-1")
db = client["smart_calendar_chatbot"]
collection = db["user_calendar"]
# Function to get user data from MongoDB by username
def get_user_data(username):
    # st.markdown(collection)
    user_data = collection.find_one({"username": username})
    if user_data:
        return user_data
    else:
        return None

# Function to update assignments in MongoDB
def update_assignments(username, updated_assignments):
    collection.update_one(
        {"username": username},
        {"$set": {"assignments": updated_assignments}}
    )

# Helper function to sort assignments by due date
def sort_assignments_by_date(assignments):
    return sorted(assignments, key=lambda x: dt.datetime.strptime(x["due_date"], "%Y-%m-%d").date())

# Helper function to group assignments by due date
def group_assignments(assignments):
    late_tasks = []
    upcoming_tasks = defaultdict(list)
    
    today = dt.date.today()

    for assignment in assignments:
        due_date = dt.datetime.strptime(assignment["due_date"], "%Y-%m-%d").date()
        if due_date < today:
            late_tasks.append(assignment)
        else:
            upcoming_tasks[due_date].append(assignment)
    
    return late_tasks, dict(upcoming_tasks)

# Main form-based interface
def assignment_manager(username="kusumaj"):
    # Fetch user data from MongoDB
    user_data = get_user_data(username)
    if not user_data:
        st.error(f"No data found for user: {username}")
        return
    st.markdown(f"## Assignment Tracker for {user_data['username']} 📋")

    # Filter assignments where the status is "working"
    assignments = user_data.get("assignments", [])
    
    if not assignments:
        st.write("No assignments found.")
        return
    
    # Sort assignments by date
    sorted_assignments = sort_assignments_by_date(assignments)
    
    # Separate late tasks and upcoming tasks
    late_tasks, grouped_upcoming_tasks = group_assignments(sorted_assignments)

    # Create a session state to store which assignments are selected for completion
    if "selected_assignments" not in st.session_state:
        st.session_state["selected_assignments"] = {assignment["name"]: False for assignment in assignments}

    # Display late tasks first
    if late_tasks:
        st.markdown("### 🚨 LATE Assignments:")
        for assignment in late_tasks:
            is_selected = st.checkbox(
                f"{assignment['name']} (Due: {assignment['due_date']})",
                value=st.session_state["selected_assignments"][assignment["name"]]
            )
            st.session_state["selected_assignments"][assignment["name"]] = is_selected

    # Display upcoming tasks grouped by date
    st.markdown("### 📅 Upcoming Assignments:")
    for due_date, tasks in grouped_upcoming_tasks.items():
        st.markdown(f"#### Due: {due_date}")
        for assignment in tasks:
            is_selected = st.checkbox(
                f"{assignment['name']}",
                value=st.session_state["selected_assignments"][assignment["name"]]
            )
            st.session_state["selected_assignments"][assignment["name"]] = is_selected

    # Confirm button and action
    if st.button("Confirm", type="primary"):
        selected_for_completion = [
            assignment_name for assignment_name, completed in st.session_state["selected_assignments"].items() if completed
        ]

        # Remove selected assignments from the list
        updated_assignments = [assignment for assignment in assignments if assignment["name"] not in selected_for_completion]

        # Save the changes to MongoDB
        update_assignments(username, updated_assignments)

        # Show toast confirmation
        st.toast("Selected assignments removed!")

        # Reset the session state for checkboxes
        st.session_state["selected_assignments"] = {assignment["name"]: False for assignment in updated_assignments}
        # st.experimental_rerun()
    st.write("***")
    calendar_visualizer()

# Call the function to display the form for the user
# assignment_manager("kusumaj")

# Helper function to convert weekday names to numbers
def get_weekday_number(day_name):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days.index(day_name)

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
def calendar_visualizer():
    # Fetch user data from MongoDB
    username="kusumaj"
    user_data = get_user_data(username)
    if not user_data:
        st.error(f"No data found for user: {username}")
        return

    st.markdown(f"## Weekly Calendar for {user_data['username']} 📆")
    mode = "list"

    # Define the end date for recurrence (10th Dec 2024)
    end_date = dt.date(2024, 12, 10)
    
    # Generate recurring events for each class
    events = []
    for class_info in user_data["class_schedule"]:
        recurring_events = generate_recurring_events(class_info, end_date)
        events.extend(recurring_events)
    
    # Generate assignment events
    assignment_events = generate_assignment_events(user_data["assignments"])
    events.extend(assignment_events)
    
    # Set the initial date to today
    today_date = dt.datetime.today().strftime("%Y-%m-%d")

    calendar_options = {
        "editable": True,
        "navLinks": True,
        "initialDate": today_date,  # Set initial date to today
        "initialView": "listWeek",    # Adjust view
    }

    state = calendar(
        events=st.session_state.get("events", events),
        options=calendar_options,
        key=mode,
    )

    if state.get("eventsSet") is not None:
        st.session_state["events"] = state["eventsSet"]

# Call the function to display the calendar for the user
# username = st.text_input("Enter username:", value="kusumaj")
# if username:
#     calendar_visualizer(username)