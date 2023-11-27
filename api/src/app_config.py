from typing import Dict

APP_DEBUG = False


# TODO: Adjust prompt to indicate source of context (webpage url)
BASE_PROMPT_TEMPLATE_EN = """Answer the question based only on the following context:
{context}

Question: {question}

Answer in the following language: {language}
"""
BASE_PROMPT_TEMPLATE_NL = """Antwoord op de vraag "{question}" in het {language} met behulp van de volgende paragrafen. 
Soms is het antwoord niet letterlijk te vinden in de paragrafen en zit er een beetje creativiteit in het antwoord. 
Je mag zeker nieuwe informatie afleiden, maar zeg dit dan duidelijk in je antwoord. 
Vermeld ook relevante metadata van het document zoals "scrape_dt", "webpage_url", "webpage_title". 

START CONTEXT
{context}

START ANTWOORD


"""

BASE_PROMPT_TEMPLATE_NL_a = """Je bent een ziekenhuismedewerker en je moet op een vraag van een patiënt antwoorden op basis van paragrafen op de website van het ziekenhuis.

Beantwoord de vraag op basis van de volgende context (paragrafen op de website):
```
{context}
```

De vraag is: 
```
{question}
```

Instructies bij het antwoorden: 
- Algemeen:
    - Antwoord altijd in het {language}
    - Geef duidelijk aan als het antwoord niet gevonden kan worden in de context (paragrafen op de website). 
- Wanneer je niets vindt in de context, vermeld dan:
    - Een lijst van de meest gelijkende paragrafen op de website, idealiter met kommas gescheiden.
    - De weburl naar de paragraaf op de website. (indien gegeven)
- Wanneer je wel iets vindt in de context, vermeld dan:
    - Een Markdown lijst met de relevante context, gescheiden door komma's.
    - De weburl (bron) van de context. (indien gegeven)
"""
DEFAULT_CONFIG = {
    "temperature": 0.7,
    "context_amount": 5,
    "prompt_template": BASE_PROMPT_TEMPLATE_NL,
    "retrieval_model_selection": 1,
    "generative_model_selection": 0,
    "use_metadata": 1,
}
RETRIEVAL_CHOICES = {0: "Instructor XL", 1: "Roberta (QA - Dutch)"}
LLM_CHOICES = {0: "OpenAI", 1: "Olama LLama2"}
DATA_CHOICES = {0: "Gebruik geen metadata", 1: "Gebruik metadata"}

API_DESCRIPTION = """
Welcome to the LLM QA API 🚀
"""

QA_CORECTNESS_CHOICES = {
    0: "Antwoord is duidelijk/accuraat 👌" 
    1: "Geen mening over de duidelijkheid/accuraatheid 🙂" 
    2: "Antwoord is onduidelijk/inaccuraat 👎,"
}

QA_HELPFULNESS_CHOICES = {
    0: "Antwoord helpt mij 😀" 
    1: "Geen mening over behulpzaamheid 🙂" 
    2: "Antwoord helpt mij niet 😕" 
}
