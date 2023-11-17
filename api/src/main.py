
"""
    This is a FastAPI application that provides 
    three endpoints to query a Neo4j database and return objects as results.
"""
from typing import List
from pydantic import BaseModel
from enum import Enum
from fastapi import FastAPI
from neo4j import GraphDatabase
from langchain.vectorstores import Neo4jVector
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Neo4jVector
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA  # Q&A retrieval system.
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from operator import itemgetter

import uvicorn
import os
import langchain
from datetime import datetime
from pydantic import BaseModel

## DATA MODEL =============================================
class FeedbackEnum(str, Enum):
    """ 
        A Pydantic model representing feedback. 
    """
    like = 1
    neutral = 0
    dislike = -1

class Prompt(BaseModel):
    """
    A Pydantic model representing a LLM prompt
    """
    prompt: str

class Question(BaseModel):
    """
    A Pydantic model representing a search question. 
    """
    search_string: str

class ChunkMetadata(BaseModel):
    """
    A Pydantic model representing metadata.
    """
    chunk_size: int
    embedding_model: str
    chunk_order: int
    chunk_overlap: int
    chunk_id: int

class Document(BaseModel):
    """
    A Pydantic model representing a document.
    Wrapper around langchains langchain.schema.document.Document.
    """
    page_content: str
    metadata: ChunkMetadata

class Answer(BaseModel):
    """
    A Pydantic model representing an answer to a question.
    """
    context: List[Document]
    llm_prompt: str
    llm_answer: str
    language: str
    score: FeedbackEnum

## API INSTANTIATION =============================================
#### CONSTANTS ========================
API_DESCRIPTION = """
Welcome to the LLM FAQ API 🚀

## API Requirements
- Search clearly indicates when the question cannot be found in the database. 
    - Clearly indicate "the answer cannot be found"
    - Search Query is written to Neo4j, as a "bad" chat. 
        - This can notify the hospital that there was a question that could not be answered 
- A way to rate the answers given by the search interface. 
    - By default, ratings are neutral.
    - The user can upvote or downvote the answer. This is written back to Neo4j. (Like ChatGPT)
- A way for to search historical answers 
- A way to correct bad answers.  

### Interfaces     
- Interface for hospital to visualize search interactions:
    - ✅ see [Neodash](http://20.111.32.34:5005/)
- Interface for hospital to seach & correct bad answers.

## Implementation 
* **Generate Answer**: `answer/generate`(TODO)
* **Score Answers**: `answer/score` (TODO)
* **Search Answers**: `answer/search` (TODO)
* **Correct Answers**: `answer/correct` (TODO)
"""
BASE_PROMPT_TEMPLATE = """
Answer the question based only on the following context:
{context}

Question: {question}

Answer in the following language: {language}
"""
    # Define the configuration
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

#### GLOBAL VARIABLES =================
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

# Instructor Embeddings
embeddings = HuggingFaceInstructEmbeddings(
    model_name="hkunlp/instructor-xl", 
    cache_folder='./src/models'
)

# Graph from existing graph
neo4j_graph = Neo4jVector.from_existing_index(
    embedding=embeddings,
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    index_name="vi_chunk_embedding_cosine",
    keyword_index_name="fts_Chunk_text",
    search_type="hybrid",
)

# Neo4j driver
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), 
    auth=(
        os.getenv("NEO4J_USER"), 
        os.getenv("NEO4J_PASSWORD")
    )
)

# Langchain retriever
neo4j_retriever = neo4j_graph.as_retriever(**RETRIEVER_SEARCH_CONFIG)

## API ENDPOINTS =============================================
@app.post('/answer/generate', status_code=201, response_model=List[Document])
def generate_answer(question: str):
    """
    Endpoint that takes in a question and generates or updates 
    a node in the Neo4j database.

    Args:
        chat_object (ChatObject): A Pydantic model representing a chat object.

    Returns:
        An Answer Pydantic model representing the generated answer.
    """

    ## RETRIEVE DOCUMENTS =================
    # Get docs from Neo4j
    docs: List[langchain.schema.document.Document] = (
        neo4j_retriever.get_relevant_documents(
          question
        )
    )

    # Get Retriever Context 
    context: List[Document] = [
        Document(
            page_content=doc.page_content, 
            metadata=ChunkMetadata(
                chunk_id=doc.metadata['chunk_id'],
                chunk_size=doc.metadata['chunk_size'],
                embedding_model=doc.metadata['embedding_model'],
                chunk_order=doc.metadata['chunk_order'],
                chunk_overlap=doc.metadata['chunk_overlap']
            )
        ) for doc in docs
    ]
    
    # Generate Answer
    # llm_prompt = PromptTemplate(
    #     input_variables=["context", "question", "language"],
    #     template=BASE_PROMPT_TEMPLATE
    # )
    llm_prompt = prompt = ChatPromptTemplate.from_template(BASE_PROMPT_TEMPLATE)
    llm = ChatOpenAI()
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, 
        retriever=neo4j_retriever,
        verbose=True
    )

    def docs_to_str(l: List[langchain.schema.document.Document]) -> str:
        page_content: str = ""
        for i, d in enumerate(l): 
            # Page Content
            page_content += page_content + (
                (25 * "=") + 
                (f" Document {i+1} ") + 
                (25 * "=")
            )
            page_content += page_content + (
                (f"1. Metadata") + 
                (52 * "=" )
            )
            # Metadata 
            for k, v in d.metadata.items():
                page_content += page_content + (f"- {k}: {v}")
            
            page_content += page_content + (
                (f"2. Content") + 
                (53 * "=" )
            )
            page_content += page_content + '\n'
        return page_content
    
    print(docs_to_str(docs))

    # Get the answer to the user's question.
    llm_chain = qa_chain(
        {
            "context": itemgetter("context") | neo4j_retriever,
            "question": itemgetter("question"),
            "language": itemgetter("language"),
        }
        | llm_prompt
        | llm
        | StrOutputParser()
    )
    llm_answer = llm_chain.invoke(
        {
            "question": question, 
            "context": docs_to_str(docs), 
            "language": "dutch"
        }
    )
    return Answer(
        context=context,
        llm_prompt=BASE_PROMPT_TEMPLATE,
        llm_answer=llm_answer,
        language="dutch",
        score=FeedbackEnum.neutral
    )

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
