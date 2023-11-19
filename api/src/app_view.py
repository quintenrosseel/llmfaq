import streamlit as st
from streamlit_option_menu import option_menu

# Import your pages here
import page_configure
import page_validate
import page_view_answers

# Page configuration
st.set_page_config(page_title="QA Bot", layout="wide")

# Custom CSS
custom_css = """
    footer {
        visibility: hidden;
    }
"""

st.markdown(f'<style>{custom_css}</style>', unsafe_allow_html=True)

# Sidebar menu
with st.sidebar:
    st.text("Chat met jouw data")
    selected = option_menu(
        "", 
        [
            "Configureer", 
            "Valideer", 
            # "Toon"
        ],
        icons=[
            'gear', 
            'chat', 
            # 'eye'
        ], 
        menu_icon='arrow-down-circle-fill', 
        default_index=0
    )

# Page routing
if selected == "Configureer":
    page_configure.show()
elif selected == "Valideer":
    page_validate.show()
elif selected == "Toon":
    page_view_answers.show()
