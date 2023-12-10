import os
from app_models import QASession
import streamlit as st
import requests
from dotenv import load_dotenv
# Get environment
load_dotenv()

def handle_question(user_question: str):
    # Send a POST request with JSON data
    response = requests.get(
        os.getenv("API_URL") + "/experiment/answer/create?question=" + user_question)
    # Check the response
    if response.status_code == 201:
        print("Data posted successfully")
        return response.json()
    else:
        print("Failed to post data:", response.status_code)

def show():
    st.title("Sint Lucas FAQ Chatbot")
    user_question = st.text_input(
        label="Vraag",
        key="user_question",
        help="bvb. Wat moet ik doen voor een nieroperatie?",
        placeholder="Hoe can ik je helpen?",
    )

    if user_question:
        # Display the submitted question
        embedding = handle_question(user_question)
        st.write(embedding)
    else:
        st.write("Voer een vraag in om te beginnen.")
