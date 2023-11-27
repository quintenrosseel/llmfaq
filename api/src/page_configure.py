from typing import Dict

import streamlit as st

from app_config import DATA_CHOICES, DEFAULT_CONFIG, LLM_CHOICES, RETRIEVAL_CHOICES


def get_choice_index(m: Dict, key: str) -> int:
    """
    Get the index of a key in a dictionary.
    """
    for k, v in m.items():
        if v == key:
            return k
    return 0


def get_or_set_config() -> Dict:
    config = st.session_state.get("config", None)
    if config is None:
        config = DEFAULT_CONFIG
        st.session_state["config"] = config
    return config


def handle_config_update(key: str):
    try:
        # Get current QA sesssion
        config_val = st.session_state[key]
        st.session_state["config"][key] = config_val
    except:
        print(f"No matching key found for text field update: {key} ")
    return


# Save configuration
def save_config():
    # Save configuration to state
    st.session_state["config"] = {
        "temperature": st.session_state["temperature"],
        "context_amount": st.session_state["context_amount"],
        "prompt_template": st.session_state["prompt_template"],
        "retrieval_model_selection": get_choice_index(
            m=RETRIEVAL_CHOICES, key=st.session_state["retrieval_model_selection"]
        ),
        "generative_model_selection": get_choice_index(
            m=LLM_CHOICES, key=st.session_state["generative_model_selection"]
        ),
        "use_metadata": get_choice_index(
            m=DATA_CHOICES, key=st.session_state["use_metadata"]
        ),
    }


# print(st.session_state['config'])
def show():
    st.title("Configureer het zoeken :gear:")

    # Load config
    config: Dict[str, any] = get_or_set_config()

    col1, col2 = st.columns([1.5, 1.5])

    with col1:
        context_amount = st.number_input(
            "Hoeveelheid Context",
            min_value=1,
            max_value=5,
            key="context_amount",
            value=config["context_amount"],
            help="Hoeveel paragrafen van de website gebruiken we als context?",
        )
    with col2:
        # Configuration options
        temperature = st.slider(
            "Temperatuur",
            0.0,
            1.0,
            config["temperature"],
            key="temperature",
            step=0.1,
            help="Hoeveelheid 'creativiteit' in het antwoord",
        )

    prompt_template = st.text_area(
        "Prompt Template",
        value=config["prompt_template"],
        height=500,
        key="prompt_template",
        help="""
            De template die gebruikt wordt om het antwoord te genereren. 
            De velden {context}, {question} en {language} worden vervangen door de context, vraag en taal.
        """,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        retrieval_model_selection = st.selectbox(
            "Zoekmodel Selectie",
            options=list(RETRIEVAL_CHOICES.values()),
            index=config["retrieval_model_selection"],
            key="retrieval_model_selection",
            help="Het taalmodel dat gebruikt wordt om de context te zoeken. ",
        )

    with col2:
        generative_model_selection = st.selectbox(
            "LLM Selectie",
            options=list(LLM_CHOICES.values()),
            index=config["generative_model_selection"],
            key="generative_model_selection",
            help="Het taalmodel dat gebruikt wordt om het antwoord te genereren.",
        )
    with col3:
        # Configuration options
        use_metadata = st.selectbox(
            "Metadata Selectie",
            key="use_metadata",
            options=list(DATA_CHOICES.values()),
            index=config.get("use_metadata", 1),
            help="Gebruik metadata als context voor de LLM.",
            # on_change=handle_config_update,
            # args=['use_metadata']
        )

    # Save configuration
    def reset_config():
        st.session_state["config"] = DEFAULT_CONFIG
        st.rerun()

    col1, col2 = st.columns([1.5, 1.5])

    with col1:
        # Save to app state.
        st.button(
            ":floppy_disk: opslaan in sessie",
            on_click=save_config,
            help="Deze configuratie opslaan in de browser sessie. ",
            use_container_width=True,
            type="primary",
        )
    with col2:
        # Save to app state.
        st.button(
            ":arrows_counterclockwise: terug naar standaard",
            on_click=save_config,
            help="Reset de waarden naar de standaard configuratie ",
            use_container_width=True,
            type="primary",
        )
