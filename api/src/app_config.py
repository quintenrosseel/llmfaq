from typing import Dict

APP_DEBUG = False
BASE_PROMPT_TEMPLATE_EN = """Answer the question based only on the following context:
{context}

Question: {question}

Answer in the following language: {language}
"""

BASE_PROMPT_TEMPLATE_NL = """Je bent een ziekenhuismedewerker en je moet op een vraag van een patiënt antwoorden op basis van paragrafen op de website van het ziekenhuis.

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
    "context_amount": 3,
    "prompt_template": BASE_PROMPT_TEMPLATE_NL,
    "retrieval_model_selection": 0, 
    "generative_model_selection": 0,
    "use_metadata": 0
}
RETRIEVAL_CHOICES = {
    0: "Instructor XL", 
    1: "Roberta (QA - Dutch)"
}
LLM_CHOICES = {
    0: "OpenAI", 
    1: "Olama LLama2"
}
DATA_CHOICES = {
    0: "Gebruik metadata", 
    1: "Gebruik geen metadata"
}
RETRIEVER_SEARCH_CONFIG = {
    # "similarity" (default), "mmr", or "similarity_score_threshold".
    'search_type': 'similarity', 
    'search_kwargs': {
        # Amount of documents to return (default: 4).
        'k': 5, 
        # Amount of documents to pass to the MMR algorithm 
        # # (default: 20).
        'fetch_k': 50, 
        # Minimum relevance threshold for similarity_score_threshold.
        'score_threshold': 0, 
        # Diversity of results returned by MMR; 
        # # 1 for minimum diversity and 0 for maximum (default: 0.5).
        'lambda_mult': 0.25, 
        # Filter by document metadata.
        'filter': {'chunk_size': 500}
    }
}

API_DESCRIPTION = """
Welcome to the LLM QA API 🚀
"""