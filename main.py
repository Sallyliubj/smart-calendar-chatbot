import streamlit as st
import gemini_sample
import calendar_sample

def intro():

    st.write("# Welcome to CampusWelness! 👋")
    st.markdown("👈 Checkout the tabs and see what interest you!")
    st.sidebar.success("Select the page above.")

page_names_to_funcs = {
    "—": intro,
    
    # "Plotting Demo": plotting_demo,
    # "Mapping Demo": mapping_demo,
    # "DataFrame Demo": data_frame_demo,
    "Chatbot": gemini_sample.chatbot,
    "Tasks": calendar_sample.assignment_manager
    # calendar_sample.calendar_visualizer,
    # "Form": form.form
}


def main():
    demo_name = st.sidebar.selectbox("Select a page", page_names_to_funcs.keys())
    page_names_to_funcs[demo_name]()

# main()