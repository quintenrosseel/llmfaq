import streamlit as st
import requests
from typing import List
from app_config import DEFAULT_CONFIG, BASE_PROMPT_TEMPLATE_NL
from app_models import ChatConfig, QASession, DBResponse

# Local API
API_BASE_URL = "http://localhost:8000/"

def handle_question(user_question: str) -> QASession:
    
    # Get current QA sesssion
    session = st.session_state['current_qa_session']

    if session.user_question == user_question:
        # Don't allow multiple user questions in one session
        # User has to click feedback button first to start a new session. 
        return session

    # TODO: Some checks on user_question? 
    session.user_question = user_question
    
    # Send a POST request with JSON data
    response = requests.post(
        API_BASE_URL + 'answer/create', 
        json=session.model_dump(mode='json')
    )

    # Check the response
    if response.status_code == 201:
        # New resource created successfully
        print("Data posted successfully")
        session = QASession(**response.json())
        st.session_state['current_qa_session'] = session
        return session
    else:
        print("Failed to post data:", response.status_code)
        return session

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
    session = st.session_state['current_qa_session']

    # Send a POST request with JSON data
    response = requests.post(
        API_BASE_URL + 'answer/feedback', 
        json=session.model_dump(mode='json')
    )

    # Check the response
    if response.status_code == 201:
        # New resource created successfully
        print("Data posted successfully")

        # Reset LLM state values
        st.session_state.user_question = ''
        st.session_state.prompt = ''
        st.session_state.feedback = ''
        return DBResponse(**response.json())
    else:
        print("Failed to post data:", response.status_code)
        return DBResponse(success=False)

def handle_radio_change():
    print("Radio changed")

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
        if st.radio(
            label="llm_feedback",
            options=["I like it 😀", "It's OK 🙂", "I don't like it 😕"],
            key="llm_feedback_radio",
            label_visibility='hidden',
            on_change=handle_radio_change,
            disabled=disabled,
            horizontal=True,
                index=1):
            pass
            # TODO: Modify to allow feedback to pass through in ChatConfig object
            # st.session_state['current_qa_session'].chat_config.feed = 0
    with col2:
        if st.radio(
                label="llm_summary",
                options=["I get it 👌", "I don't get it 👎"],
                key="llm_summary_radio",
                label_visibility='hidden',
                on_change=handle_radio_change,
                disabled=disabled,
                horizontal=True):
            pass

    if st.button(
            "Save ✅", 
            key="save_feedback_button",
            help="Versturen naar de database", 
            use_container_width=True, 
            type='primary',
            disabled=disabled, 
            on_click=send_feedback):
        # Reset
        print("Verstuur de feedback")

def show():
    # Init session state
    if st.session_state.get('config', None) is None:
        st.session_state['config'] = DEFAULT_CONFIG  
    if st.session_state.get('current_qa_session', None) is None:
        config = st.session_state['config'] 
        st.session_state['current_qa_session'] = QASession(
            prompt="",  # To fill in by API
            user_question="", # To fill in by User
            chat_config=ChatConfig(
                temperature=config.get('temperature', 0.7),
                context_amount=config.get('context_amount', 3),
                prompt_template=config.get('prompt_template', BASE_PROMPT_TEMPLATE_NL),
                retrieval_model_selection=config.get('retrieval_model_selection', 0),
                generative_model_selection=config.get('generative_model_selection', 0),
                use_metadata=config.get('use_metadata', 0)
            ),
            user="dev",  # TODO, make this dynamic
            feedback="", # To fill in by User
            response=""  # To fill in by API
        ) 

    st.title("Valideer jouw data :books:")
    # st.header("Stel je vraag")
    user_question = st.text_input(
        label="Vraag",
        key="user_question",
        help="bvb. Wat moet ik doen voor een nieroperatie?", 
        placeholder="Stel een vraag over de data"
    )

    save_button_clicked = st.session_state.get('save_feedback_button', False)

    # User has submitted 
    if user_question: 
        # Check if question has changed 
        # Also check that the radios haven't been clicked
        if (not save_button_clicked):
            print("Handling new question")
            handle_question(
                user_question=user_question
            )
        show_llm_response(placeholder=st.session_state['current_qa_session'].response)
        show_feedback_widgets(disabled=False, placeholder=st.session_state['current_qa_session'].response)
    else: 
        show_llm_response()
        show_feedback_widgets(disabled=True)
    
    # Reset radio update flag
    # st.session_state['radio_update'] = False

    # st.header("Details")
    with st.expander("PARAMETERS"):
        config = st.session_state.get('config')
        if not config: 
            st.json(DEFAULT_CONFIG)
        else:
            st.json(config)


