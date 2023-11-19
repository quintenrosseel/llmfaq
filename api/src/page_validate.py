import streamlit as st
import requests
from typing import List
from app_config import DEFAULT_CONFIG, BASE_PROMPT_TEMPLATE_NL
from app_models import ChatConfig, FeedbackEnum, QASession


def handle_question(user_question: str):
    
    # Get RAG configuration 
    config = st.session_state['config'] 

    # Define the URL of your local API
    url = "http://localhost:8000/answer/generate"

    data = QASession(
        prompt="",  # To fill in by API
        user_question=user_question,
        chat_config=ChatConfig(
            temperature=config.get('temperature', 0.5),
            context_amount=config.get('context_amount', 3),
            prompt_template=config.get('prompt_template', BASE_PROMPT_TEMPLATE_NL),
            retrieval_model_selection=config.get('retrieval_model_selection', 0),
            generative_model_selection=config.get('generative_model_selection', 0)
        ),
        user="dev",  # TODO, make this dynamic
        feedback="<>", # To fill in by User
        response="<>"  # To fill in by API
    )
    
    print(data)

    # Send a POST request with JSON data
    response = requests.post(url, json=QASession().model_dump(mode='json'))

    # Check the response
    if response.status_code == 200:
        print("Data posted successfully")
        print(response.json())
    else:
        print("Failed to post data:", response.status_code)

    # Generate Answer with API call 
    # TODO: add retrieval and generation logic here

    # Call API with user question to get answer 
    
    # st.session_state['current_qa_session'] = 

def show_llm_response(placeholder: str = "Antwoord van de chatbot"): 
    return st.text_area(
        value=placeholder, 
        label="Antwoord", 
        height=150, 
        placeholder=placeholder,
        help="Antwoord van de chatbot, je kan dit aanpassen als het niet correct is. ", 
        disabled=True
    )

def send_feedback(): 
    st.session_state.user_question = ''

def show_feedback_widgets(disabled: bool = False, placeholder: str = "Correctie"):
    # Placeholder for database response
    st.text_area(
        value=placeholder,  
        label="Correctie & feedback",
        key=f"llm_response_feedback_{str(disabled)}", 
        height=150, 
        placeholder=placeholder,
        help="Pas het antwoord aan als het niet correct is", 
        disabled=disabled
    )

    col1, col2, = st.columns([1.5, 1.5])

    with col1:
        st.radio(
            label="llm_feedback",
            options=["I like it 😀", "It's OK 🙂", "I don't like it 😕"],
            key="llm_feedback",
            label_visibility='hidden',
            disabled=disabled,
            horizontal=True,
            index=1
        )
    with col2:
        st.radio(
            label="llm_summary",
            options=["I get it 👌", "I don't get it 👎"],
            key="llm_summary",
            label_visibility='hidden',
            disabled=disabled,
            horizontal=True
        )
    if st.button(
            "Save ✅", 
            help="Versturen naar de database", 
            use_container_width=True, 
            type='primary',
            disabled=disabled, on_click=send_feedback):
        # Reset
        print("Reset")

def show():
    # Init session state
    if st.session_state.get('config', None) is None:
        st.session_state['config'] = DEFAULT_CONFIG 

    st.title("Valideer jouw data :books:")
    # st.header("Stel je vraag")
    user_question = st.text_input(
        label="Vraag",
        key="user_question",
        help="bvb. Wat moet ik doen voor een nieroperatie?", 
        placeholder="Stel een vraag over de data"
    )

    if user_question: 
        handle_question(
            user_question=user_question
        )
        show_llm_response(placeholder=st.session_state['current_qa_session'].response)
        show_feedback_widgets(disabled=False, placeholder=st.session_state['current_qa_session'].response)
    else: 
        show_llm_response()
        show_feedback_widgets(disabled=True)

    # st.header("Details")
    with st.expander("PARAMETERS"):
        config = st.session_state.get('config')
        if not config: 
            st.json(DEFAULT_CONFIG)
        else:
            st.json(config)


