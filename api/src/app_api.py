import os
from datetime import datetime
from typing import List

import langchain
import numpy as np
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain.chains import RetrievalQA  # Q&A retrieval system.
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import (HuggingFaceEmbeddings,
                                  OpenAIEmbeddings,
                                  HuggingFaceInstructEmbeddings)
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.vectorstores import Neo4jVector
from neo4j import GraphDatabase
from neomodel import (ArrayProperty, FloatProperty, IntegerProperty,
                      RelationshipTo, StringProperty, StructuredNode,
                      UniqueIdProperty, config, db)
from neomodel.contrib import SemiStructuredNode
from neomodel.core import NodeClassAlreadyDefined
from pydantic import BaseModel

from app_api_helpers import (chunk_paths_to_docs, docs_to_str,
                             get_neo4j_node_paths, question_to_context)
from app_config import API_DESCRIPTION, APP_DEBUG, BASE_PROMPT_TEMPLATE_NL
from app_models import DBResponse, QASession

load_dotenv()

openai = OpenAIEmbeddings(
    openai_api_key="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",
    model="text-embedding-ada-002" 
)

"""
    This is a FastAPI application that provides 
    three endpoints to query a Neo4j database and return objects as results.
"""

#### Configure Environment =================
if APP_DEBUG:
    langchain.verbose = True
    langchain.debug = True



# TODO: add simple API call that doesn't use a self-hosted LLM. 

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
model_kwargs = {"device": "cpu"}
encode_kwargs = {
    # 'normalize_embeddings': True,
    "show_progress_bar": False
}

#### DB =================
# driver = GraphDatabase.driver(
#     os.getenv("NEO4J_URI"),
#     auth=(
#         os.getenv("NEO4J_USER"),
#         os.getenv("NEO4J_PASSWORD")
#     )
# )


# Neo4j Neomodel
class Chunk(StructuredNode):
    chunk_id = IntegerProperty()
    embedding_model = StringProperty()
    embedding = ArrayProperty()
    text = StringProperty()
    chunk_order = IntegerProperty()
    chunk_size = IntegerProperty()
    chunk_overlap = IntegerProperty()
    next_chunk = RelationshipTo("Chunk", "NEXT_CHUNK")

class Answer(StructuredNode):
    answer_id = IntegerProperty()
    text = StringProperty()

class QA(StructuredNode):
    config_temperature = FloatProperty()
    config_context_amount = IntegerProperty()
    config_prompt_template = StringProperty()
    config_retrieval_model_selection = IntegerProperty()
    config_generative_model_selection = IntegerProperty()
    config_use_metadata = IntegerProperty()
    user_question = StringProperty()
    correction = StringProperty()
    corectness = IntegerProperty()
    helpfulness = IntegerProperty()
    prompt = StringProperty()
    user = StringProperty()
    feedback = StringProperty()
    response = StringProperty()
    timestamp = StringProperty()
    related_chunk = RelationshipTo("Chunk", "HAS_RETRIEVED")


# config.DRIVER = driver
# config.DATABASE_NAME = os.getenv("NEO4J_DB"),
# db.set_connection(driver=driver)
config.DATABASE_URL = (
    f"bolt://{os.getenv('NEO4J_USER')}:{os.getenv('NEO4J_PASSWORD')}@"
    + os.getenv("NEO4J_URI").replace("bolt://", "").replace("/:7687", ":7687/neo4j")
)

# TODO: Check if DB URL config is needed
# Using URL - auto-managed
db.set_connection(url=config.DATABASE_URL)

def get_related_answer(question_id):
    # Cypher query to match the question node by question_id and retrieve the related answer node
    query = """
    MATCH (q:Question)-[:HAS_ANSWER]->(a:Answer)
    WHERE q.question_id = $question_id
    RETURN a
    """
    results, meta = db.cypher_query(query, params={"question_id": question_id})
    # Assuming 'Answer' is a StructuredNode that represents the answer node in Neo4j
    answer_nodes = [Answer.inflate(row[0]) for row in results]
    return answer_nodes[0] if answer_nodes else None

def get_retrieval_db(retriever_type: str = "qa") -> Neo4jVector:
    """
    Don't use global variables to avoid DB connection timeouts.
    """
    if retriever_type == "experiment":
        embedding = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model="text-embedding-ada-002"
        )
        return Neo4jVector.from_existing_index(
            embedding=embedding,
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USER"),
            password=os.getenv("NEO4J_PASSWORD"),
            index_name="vi_question_text_embedding_cosine_1536",
            # keyword_index_name="fts_Chunk_text",
            # search_type="hybrid",
        )
    else:
        "Invalid retriever type."


## API ENDPOINTS =============================================
QA_SESSION = None


# openai = OpenAIEmbeddings(
#     openai_api_key=os.getenv("OPENAI_API_KEY"),
#     model="text-embedding-ada-002" 
# )

@app.get("/experiment/answer/create", status_code=201, response_model=object)
def create_experiment_answer(question: str):
    """
    Endpoint that takes in a question and generates an answer.
    Args:
        question (str): A string representing a question.
    Returns a string
    """
    # query_embedding = openai.embed_query(question)
    graph = get_retrieval_db(retriever_type="experiment")
    retriever = graph.as_retriever(search_type="similarity")
    retrieved_nodes = retriever.get_relevant_documents(question)  # Retrieve the top 0 node

    if retrieved_nodes:
        answer = get_related_answer(retrieved_nodes[0].metadata["question_id"])
        return answer.text 
    else:
        return {"error": "No matching node found."}

def get_all_answers():
    query = """
    MATCH (a:Answer)
    RETURN a.answer_id, properties(a)
    """
    results, _ = db.cypher_query(query)
    embeddings = openai.embed_documents([answer_props.get("text", "") for answer_id, answer_props in results])
    # Merge embeddings with answer properties and return the combined data
    merged_results = [
        {**answer_props, "embedding": embedding}
        for (answer_id, answer_props), embedding in zip(results, embeddings)
    ]
    return merged_results

# embeddings are list of numbers
def cosine_similarity(embedding1, embedding2):
    # Normalize the embeddings
    embedding1 = np.array(embedding1) / np.linalg.norm(embedding1)
    embedding2 = np.array(embedding2) / np.linalg.norm(embedding2)
    # Compute the cosine similarity
    similarity = np.dot(embedding1, embedding2)
    return similarity

def cosine_distance(embedding1, embedding2):
    return 1 - cosine_similarity(embedding1, embedding2)


@app.get("test_results", status_code=201, response_model=object)
def get_all_questions():
    query = """
    MATCH (q:Question)
    RETURN q.question_id, properties(q)
    """
    results, _ = db.cypher_query(query)
    return results

def test():
    questions = get_all_questions()
    answers = get_all_answers()

    for question_id, question  in questions:
        distances = []
        for answer in answers:
            distance = cosine_distance(question["text_embedding"], answer["embedding"])
            distances.append({ "answer": answer, "distance": distance })
        # get the answer with the lowest distance
        distances = sorted(distances, key=lambda x: x["distance"])
        min_distance = distances[0]
        print(f"Question: {question['text']}\nArchetype question: {min_distance['answer']['question_archetype']}\n\nBest Answer: {min_distance['answer']['text']}\nDistance: {min_distance['distance']}")
        distances_str = " - ".join(str(distance['distance']) for distance in distances)
        print(distances_str)


    for question_id, props  in results:
        # relationships = get_question_relationships(question_id)
        question_string = props["text"]
        question_archetype_embedding = get_question_archetype_embedding(question_id)
        answer = create_experiment_answer(question_string)
        # Process each question here
        # print(f"Question ID: {question_id}, Text: {text}, Embedding: {embedding}")
test()

def get_question_archetype_embedding(question_id):
    # Step 1: Get the archetype_question property from the answer
    archetype_query = """
    MATCH (q:Question)-[:HAS_ANSWER]->(a:Answer)
    WHERE q.question_id = $question_id
    RETURN a.question_archetype
    """
    archetype_result, _ = db.cypher_query(archetype_query, params={"question_id": question_id})
    if archetype_result:
        archetype_question_text = archetype_result[0][0]

        # Step 2: Get the embedding for the archetype question
        embedding_query = """
        MATCH (q:Question)
        WHERE q.text = $archetype_question_text
        RETURN q.question_id, properties(q)
        """
        embedding_result, _ = db.cypher_query(embedding_query, params={"archetype_question_text": archetype_question_text})
        if embedding_result:
            return np.array(embedding_result[0][0])
    return None

get_all_questions()

# def flag_questions_not_closest_to_archetype():
#     questions_embeddings = get_all_questions_embeddings()
#     flagged_questions = {}

#     for question_id, embedding in questions_embeddings.items():
#         archetype_embedding = get_question_archetype_embedding(question_id)
#         if archetype_embedding is not None:
#             similarity = cosine_similarity([embedding], [archetype_embedding])[0][0]
#             # Assuming you have a threshold to determine if the question is "close enough"
#             threshold = 0.5  # Set your own threshold
#             if similarity < threshold:
#                 flagged_questions[question_id] = similarity

#     return flagged_questions

# Example usage:
# flagged_questions = flag_questions_not_closest_to_archetype()
# for question_id, similarity in flagged_questions.items():
#     print(f"Question ID: {question_id} is not closest to the archetype with similarity: {similarity}")        

def get_question_relationships(question_id):
    query = """
    MATCH (q:Question)-[r]->(relatedNode)
    WHERE q.question_id = $question_id
    RETURN type(r) as relationshipType, properties(relatedNode) as relatedProps
    """
    results, _ = db.cypher_query(query, params={"question_id": question_id})
    for relationship_type, related_props in results:
        # Process each relationship and related node properties here
        print(f"Relationship Type: {relationship_type}, Related Node Properties: {related_props}")



# TODO: Add auto-merge pipeline
# TODO: Add Translation Interface
@app.post("/answer/create", status_code=201, response_model=QASession)
def create_answer(session: QASession):
    """
    Endpoint that takes in a QA Session and generates an answer.

    Args:
        session (QASession): A Pydantic model representing a chat session.

    Returns:
        An Answer Pydantic model representing the generated answer.
    """
    q = session.user_question
    print(session)
    # TODO: Add MMR algorithm ability
    retriever_search_config = {
        # "similarity" (default), "mmr", or "similarity_score_threshold".
        "search_type": "similarity",
        "search_kwargs": {
            # Amount of documents to return (default: 4).
            "k": session.chat_config.context_amount,
            # Amount of documents to pass to the MMR algorithm
            # # (default: 20).
            "fetch_k": 50,
            # Minimum relevance threshold for similarity_score_threshold.
            "score_threshold": 0,
            # Diversity of results returned by MMR;
            # # 1 for minimum diversity and 0 for maximum (default: 0.5).
            "lambda_mult": 0.25,
            # Filter by document metadata.
            "filter": {"chunk_size": 500},
        },
    }

    # Set retriever based on config (0 = QA, 1 = Retrieval Model)
    if session.chat_config.retrieval_model_selection == 0:
        graph = get_retrieval_db(retriever_type="qa")
        retriever = graph.as_retriever(**retriever_search_config)
        model = robbert_model
        embedding_index = "vi_chunk_qa_embedding_cosine"
    else:
        graph = get_retrieval_db(retriever_type="retrieval")
        retriever = graph.as_retriever(**retriever_search_config)
        model = instructor_model
        embedding_index = "vi_chunk_retrieval_embedding_cosine"

    # TODO: Check for Mistral / LLama2 open source models.
    # 0 = OpenAI, 1 is Olama
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo-16k",
        temperature=session.chat_config.temperature,
    )

    llm_prompt = PromptTemplate(
        input_variables=["context", "question", "language"],
        template=session.chat_config.prompt_template,
    )

    llm_chain = LLMChain(prompt=llm_prompt, llm=llm, verbose=APP_DEBUG)

    # TODO: Add QA session as additional context (if available)
    # Set metadata based on config (1 = Use, 0 = Don't use)
    if session.chat_config.use_metadata == 0:
        # Get relevant documents, without context (langchain)
        docs: List[
            langchain.schema.document.Document
        ] = retriever.get_relevant_documents(q)
        include_metadata = False
    else:
        # GEt relevant documents, with context (manual)
        docs: List[langchain.schema.document.Document] = question_to_context(
            question=q,
            graph=graph,
            limit=session.chat_config.context_amount,
            embedding_model=model,
            embedding_index=embedding_index,
            to_str=False,
        )
        include_metadata = True

    llm_answer = llm_chain.invoke(
        input={
            "question": q,
            "context": docs_to_str(
                docs,
                include_metadata=include_metadata,
                skip_meta_keys=[
                    "chunk_id",
                    "chunk_order",
                    "chunk_overlap",
                    "chunk_size",
                    "qa_embedding_model",
                    "retrieval_embedding_model",
                    "qa_embedding",
                    "retrieval_embedding",
                ],
            ),
            "language": "Nederlands",
        },
        return_only_outputs=False,
        include_run_info=True,
    )

    print(session.chat_config.prompt_template.format_map(llm_answer))

    chunk_ids: List[int] = [doc.metadata["chunk_id"] for doc in docs]
    return QASession(
        prompt=session.chat_config.prompt_template.format_map(llm_answer),
        user_question=session.user_question,
        chat_config=session.chat_config,
        user=session.user,
        helpfulness=session.helpfulness,
        corectness=session.corectness,
        correction=llm_answer["text"],
        feedback=session.feedback,
        response=llm_answer["text"],
        chunk_ids=chunk_ids,
        timestamp=session.timestamp,
    )


@app.post("/answer/feedback", status_code=201, response_model=DBResponse)
def create_answer_feedback(session: QASession):
    """
    Endpoint that takes in a QA Session and generates an answer.

    Args:
        session (QASession): A Pydantic model representing a chat session.

    Returns:
        An Answer Pydantic model representing the DB Response.
    """

    # Save QA nodes to DB
    qa = QA(
        config_temperature=session.chat_config.temperature,
        config_context_amount=session.chat_config.context_amount,
        config_prompt_template=session.chat_config.prompt_template,
        config_retrieval_model_selection=session.chat_config.retrieval_model_selection,
        config_generative_model_selection=session.chat_config.generative_model_selection,
        config_use_metadata=session.chat_config.use_metadata,
        user_question=session.user_question,
        prompt=session.prompt,
        user=session.user,
        helpfulness=session.helpfulness,
        corectness=session.corectness,
        feedback=session.feedback,
        response=session.response,
        correction=session.correction,
        chunk_ids=session.chunk_ids,
        timestamp=session.timestamp,
    )

    # Save in DB
    qa.save()

    for chunk_id in session.chunk_ids:
        chunk = Chunk.nodes.get_or_none(chunk_id=chunk_id)
        if chunk is not None:
            qa.related_chunk.connect(chunk)
        else:
            print(f"Chunk with id {chunk_id} not found in DB")

    return DBResponse(success=True)


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
