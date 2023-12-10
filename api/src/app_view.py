import streamlit as st
from streamlit_option_menu import option_menu

# Import your pages here
import page_configure
import page_qa
import validated_qa_experiment

# import page_view_answers

# Page configuration
st.set_page_config(page_title="QA Bot", layout="wide")

# Custom CSS
custom_css = """
    footer {
        visibility: hidden;
    }
"""

st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# TODO: Add interface to chat with the bot in interactive mode.
# Sidebar menu
with st.sidebar:
    st.text("Chat met jouw data")
    selected = option_menu(
        "",
        [
            "Configureer",
            "Chat",
            "Validated QA experiment"
            # "Toon"
        ],
        icons=[
            "gear",
            "chat",
            # 'eye'
        ],
        menu_icon="arrow-down-circle-fill",
        default_index=2,
    )

# Page routing
if selected == "Configureer":
    page_configure.show()
elif selected == "Chat":
    page_qa.show()
elif selected == "Validated QA experiment":
    validated_qa_experiment.show()
# elif selected == "Toon":
#     page_view_answers.show()
