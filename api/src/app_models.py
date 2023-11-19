from pydantic import BaseModel
from enum import Enum
from typing import List

class FeedbackEnum(str, Enum):
    """ 
        A Pydantic model representing feedback. 
    """
    like = 1
    neutral = 0
    dislike = -1

class ChatConfig(BaseModel):
    """
    A Pydantic model representing the configuration of the chatbot.
    """
    temperature: float
    context_amount: int
    prompt_template: str
    retrieval_model_selection: int
    generative_model_selection: int
    # TODO: add metadata selection here

class QASession(BaseModel):
    """
    A Pydantic model representing a chat message.
    """
    chat_config: ChatConfig
    user_question: str
    prompt: str
    user: str 
    feedback: str
    response: str 


# NEEDED? 
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