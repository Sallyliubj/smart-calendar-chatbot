def chatbot():
    from dotenv import load_dotenv
    import streamlit as st
    import os
    import google.generativeai as ggi

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
    st.title("Chat with your Gemini-Powered Assistant!")

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