import os
from datetime import datetime
from typing import List

import requests
import streamlit as st
from dotenv import load_dotenv

from app_config import (
    BASE_PROMPT_TEMPLATE_NL,
    DEFAULT_CONFIG,
    QA_CORECTNESS_CHOICES,
    QA_HELPFULNESS_CHOICES,
)
from app_models import ChatConfig, DBResponse, QASession
from page_configure import get_choice_index

# Get environment
load_dotenv()


# TOOD: Add Streaming to the QA
def handle_question(user_question: str) -> QASession:
    """_summary_

    Args:
        user_question (str): _description_

    Returns:
        QASession: _description_
    """
    # Get current QA sesssion
    qa_session = st.session_state["current_qa_session"]

    if qa_session.user_question == user_question:
        # Don't allow multiple user questions in one qa_session
        # User has to click feedback button first to start a new qa_session.
        return qa_session

    # TODO: Some checks on user_question?
    qa_session.user_question = user_question

    # Send a POST request with JSON data
    response = requests.post(
        os.getenv("API_URL") + "/answer/create", json=qa_session.model_dump(mode="json")
    )

    # Check the response
    if response.status_code == 201:
        # New resource created successfully
        print("Data posted successfully")
        qa_session = QASession(**response.json())
        st.session_state["current_qa_session"] = qa_session
        return qa_session
    else:
        print("Failed to post data:", response.status_code)
        return qa_session


def show_llm_response(placeholder: str = "Antwoord van de chatbot"):
    return st.text_area(
        value=placeholder,
        label="Antwoord",
        height=150,
        placeholder=placeholder,
        help="Antwoord van de chatbot, je kan dit aanpassen als het niet correct is. ",
        disabled=True,
    )


def send_feedback():
    qa_session = st.session_state["current_qa_session"]

    # Send a POST request with JSON data
    response = requests.post(
        os.getenv("API_URL") + "/answer/feedback",
        json=qa_session.model_dump(mode="json"),
    )

    # Check the response
    if response.status_code == 201:
        # New resource created successfully
        print("Data posted successfully")

        # Reset LLM state values
        st.session_state.user_question = ""
        st.session_state.prompt = ""
        st.session_state.correction = ""
        st.session_state.feedback = ""
        st.session_state.helpfulness = 1
        st.session_state.corectness = 1
        return DBResponse(**response.json())
    else:
        print("Failed to post data:", response.status_code)
        return DBResponse(success=False)


def handle_radio_change_helpfulness():
    # Get current QA sesssion
    qa_session_helpfulness = st.session_state["qa_helpfulness_radio"]
    helpfulness_idx: int = get_choice_index(
        m=QA_HELPFULNESS_CHOICES, key=qa_session_helpfulness
    )
    st.session_state["current_qa_session"].helpfulness = helpfulness_idx


def handle_radio_change_corectness():
    # Get current QA sesssion
    qa_session_corectness = st.session_state["qa_corectness_radio"]
    corectness_idx: int = get_choice_index(
        m=QA_CORECTNESS_CHOICES, key=qa_session_corectness
    )
    st.session_state["current_qa_session"].corectness = corectness_idx


def handle_text_field_update(key: str):
    # Get current QA sesssion
    qa_session_textval = st.session_state[key]
    # Handle
    if "llm_feedback" in key:
        st.session_state["current_qa_session"].feedback = qa_session_textval
        return
    elif "llm_correction" in key:
        st.session_state["current_qa_session"].correction = qa_session_textval
        return
    else:
        print(f"No matching key found for text field update: {key} ")


def show_feedback_widgets(
    disabled: bool = False, placeholder: str = "Corrigeer dit antwoord"
):
    # Placeholder for database response
    st.text_area(
        value=placeholder,
        label="Correctie",
        key=f"llm_correction_{str(disabled)}",
        height=150,
        placeholder=placeholder,
        help="Pas het antwoord aan als het niet correct is",
        disabled=disabled,
        on_change=lambda is_disabled: handle_text_field_update(
            key=f"llm_correction_{str(disabled)}"
        ),
        args=[disabled],
    )

    # Placeholder for feedback
    st.text_area(
        label="Feedback",
        key=f"llm_feedback_{str(disabled)}",
        height=50,
        placeholder="Geef feedback op het antwoord",
        help="Feedback op dit antwoord?",
        disabled=disabled,
        on_change=lambda is_disabled: handle_text_field_update(
            key=f"llm_feedback_{str(disabled)}"
        ),
        args=[disabled],
    )

    (
        col1,
        col2,
    ) = st.columns([1.5, 1.5])

    with col1:
        helpfulness = st.radio(
            label="llm_helpfulness",
            options=list(QA_HELPFULNESS_CHOICES.values()),
            key="qa_helpfulness_radio",
            label_visibility="hidden",
            on_change=handle_radio_change_helpfulness,
            disabled=disabled,
            horizontal=False,
            index=st.session_state["current_qa_session"].helpfulness,
        )

    with col2:
        corectness = st.radio(
            label="llm_corectness",
            options=list(QA_CORECTNESS_CHOICES.values()),
            key="qa_corectness_radio",
            label_visibility="hidden",
            on_change=handle_radio_change_corectness,
            disabled=disabled,
            horizontal=False,
            index=st.session_state["current_qa_session"].corectness,
        )

    if st.button(
        "Save ✅",
        key="save_feedback_button",
        help="Versturen naar de database",
        use_container_width=True,
        type="primary",
        disabled=disabled,
        on_click=send_feedback,
    ):
        # Reset
        print("Verstuur de feedback")


def show():
    # Init session state
    if st.session_state.get("config", None) is None:
        st.session_state["config"] = DEFAULT_CONFIG
    if st.session_state.get("current_qa_session", None) is None:
        config = st.session_state["config"]
        st.session_state["current_qa_session"] = QASession(
            prompt="",  # To fill in by API
            user_question="",  # To fill in by User
            chat_config=ChatConfig(
                temperature=config.get("temperature", 0.7),
                context_amount=config.get("context_amount", 3),
                prompt_template=config.get("prompt_template", BASE_PROMPT_TEMPLATE_NL),
                retrieval_model_selection=config.get("retrieval_model_selection", 0),
                generative_model_selection=config.get("generative_model_selection", 0),
                use_metadata=config.get("use_metadata", 1),
            ),
            user="dev",  # TODO, make this dynamic
            helpfulness=1,  # To fill in by User
            corectness=1,  # To update by User
            feedback="",  # To update by User
            response="",  # LLM respnse to fill in by API
            correction="",  # To fill in by User
            chunk_ids=[],  # To fill in by API
            timestamp=(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        )

    st.title("Chat met jouw data :books:")
    # st.header("Stel je vraag")
    user_question = st.text_input(
        label="Vraag",
        key="user_question",
        help="bvb. Wat moet ik doen voor een nieroperatie?",
        placeholder="Stel een vraag over de data",
    )

    save_button_clicked = st.session_state.get("save_feedback_button", False)

    # User has submitted
    if user_question:
        # Check if question has changed
        # Also check that the radios haven't been clicked
        if not save_button_clicked:
            handle_question(user_question=user_question)
        show_llm_response(placeholder=st.session_state["current_qa_session"].response)
        show_feedback_widgets(
            disabled=False, placeholder=st.session_state["current_qa_session"].response
        )
    else:
        show_llm_response()
        show_feedback_widgets(disabled=True)

    # Reset radio update flag
    # st.session_state['radio_update'] = False

    # st.header("Details")
    with st.expander("PARAMETERS"):
        config = st.session_state.get("config")
        if not config:
            st.json(DEFAULT_CONFIG)
        else:
            st.json(config)
