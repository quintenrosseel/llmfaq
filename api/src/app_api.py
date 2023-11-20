from typing import List
from fastapi import FastAPI
from neo4j import GraphDatabase
from langchain.vectorstores import Neo4jVector
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Neo4jVector
from langchain.embeddings import HuggingFaceInstructEmbeddings, HuggingFaceEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA  # Q&A retrieval system.
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from app_config import (API_DESCRIPTION, APP_DEBUG, RETRIEVER_SEARCH_CONFIG, BASE_PROMPT_TEMPLATE_NL)
from app_models import (QASession, DBResponse)
from app_api_helpers import (docs_to_str, chunk_paths_to_docs, get_neo4j_node_paths, question_to_context)

import uvicorn
import os
import langchain
from datetime import datetime
from pydantic import BaseModel
from langchain.chains import LLMChain

"""
    This is a FastAPI application that provides 
    three endpoints to query a Neo4j database and return objects as results.
"""

#### Configure Environment =================
if APP_DEBUG: 
    langchain.verbose = True
    langchain.debug = True

load_dotenv() 

# FastAPI
app = FastAPI(
    title="LLM FAQ API",
    description=API_DESCRIPTION,
    summary="Generate Accurate Responses Backed by a Knowledge Base",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Quinten Rosseel",
        "email": "quinten.rosseel@ghotmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


#### NLP Models =================
model_kwargs = {
    'device': 'cpu'
}

encode_kwargs = {
    # 'normalize_embeddings': True,
    'show_progress_bar': False
}

instructor_model = HuggingFaceInstructEmbeddings(
    model_name="hkunlp/instructor-xl", 
    cache_folder='src/models/hkunlp_instructor-xl',
    embed_instruction="Represent the Medical question for retrieving supporting paragraphs: ",
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

robbert_model = HuggingFaceEmbeddings(
    model_name="jegorkitskerkin/robbert-v2-dutch-base-mqa-finetuned", 
    cache_folder='src/models/robbert-v2-dutch-base-mqa-finetuned',
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

#### DB =================
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), 
    auth=(
        os.getenv("NEO4J_USER"), 
        os.getenv("NEO4J_PASSWORD")
    )
)

# QA with robbert model 
neo4j_qa_graph = Neo4jVector.from_existing_index(
    embedding=robbert_model,
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    index_name="vi_chunk_qa_embedding_cosine",
    keyword_index_name="fts_Chunk_text",
    search_type="hybrid",
)

# Retrieval with instructor model
neo4j_retrieval_graph = Neo4jVector.from_existing_index(
    embedding=instructor_model,
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    index_name="vi_chunk_retrieval_embedding_cosine",
    keyword_index_name="fts_Chunk_text",
    search_type="hybrid",
)

## API ENDPOINTS =============================================
QA_SESSION = None
@app.post('/answer/create', status_code=201, response_model=QASession)
def create_answer(session: QASession):
    """
    Endpoint that takes in a QA Session and generates an answer. 

    Args:
        session (QASession): A Pydantic model representing a chat session.

    Returns:
        An Answer Pydantic model representing the generated answer.
    """
    q = session.user_question   
    # if QA_SESSION and QA_SESSION.user_question == q:
    #     return q

    # Set retriever based on config (0 = QA, 1 = Retrieval Model)
    if session.chat_config.retrieval_model_selection == 0:
        graph = neo4j_qa_graph
        retriever = graph.as_retriever(**RETRIEVER_SEARCH_CONFIG)
        model = robbert_model
        embedding_index = "vi_chunk_qa_embedding_cosine"
    else:
        graph = neo4j_retrieval_graph
        retriever = graph.as_retriever(**RETRIEVER_SEARCH_CONFIG)
        model = instructor_model
        embedding_index = "vi_chunk_retrieval_embedding_cosine"
    
    # TODO: set LLM based on config 
    # Set temperature for LLM
    llm = ChatOpenAI(
        temperature=session.chat_config.temperature,
    )

    llm_prompt = PromptTemplate(
        input_variables=["context", "question", "language"],
        template=session.chat_config.prompt_template
    )

    llm_chain = LLMChain(
        prompt=llm_prompt, 
        llm=llm,
        verbose=APP_DEBUG
    )
    
    # Set metadata based on config (0 = Use, 1 = Don't use)
    if session.chat_config.use_metadata == 0:
        # Get relevant documents, without context (langchain)
        docs: List[langchain.schema.document.Document] = (
            retriever.get_relevant_documents(q)
        )
        include_metadata = True
    else:
        # GEt relevant documents, with context (manual)
        docs: List[langchain.schema.document.Document] = question_to_context(
            question=q, 
            graph=neo4j_qa_graph,
            limit=session.chat_config.context_amount,
            embedding_model=model,
            embedding_index=embedding_index,
            to_str=False
        ) 
        include_metadata=False

    llm_answer = llm_chain.invoke(
        input={
            "question": q,
            "context": docs_to_str(
                docs,
                include_metadata=False, 
                skip_meta_keys=[
                    'chunk_id', 
                    'chunk_order', 
                    'chunk_overlap', 
                    'chunk_size', 
                    'qa_embedding_model', 
                    'retrieval_embedding_model'
                ]
            ),
            "language": "Nederlands"
        },
        return_only_outputs=False,
        include_run_info=True
    )

    # CACHE QA SESSION 

    #TODO: Add explicit link to chunks
    return QASession(
        prompt=session.chat_config.prompt_template.format_map(llm_answer),
        user_question=session.user_question,
        chat_config=session.chat_config,
        user=session.user, 
        feedback=session.feedback,
        response=llm_answer['text']
    )

@app.post('/answer/feedback', status_code=201, response_model=DBResponse)
def create_answer_feedback(session: QASession):
    """
    Endpoint that takes in a QA Session and generates an answer. 

    Args:
        session (QASession): A Pydantic model representing a chat session.

    Returns:
        An Answer Pydantic model representing the DB Response. 
    """
    
    print("Saving to database...")

    print("Success!")
    # TODO: save to database! 
    return DBResponse(
        success=True
    )

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
