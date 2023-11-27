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
    use_metadata: int

class QASession(BaseModel):
    """
    A Pydantic model representing a chat message.
    """
    timestamp: str
    chat_config: ChatConfig
    user_question: str
    prompt: str
    response: str 
    user: str 
    helpfulness: int
    corectness: int
    feedback: str
    correction: str
    chunk_ids: List[int]

class DBResponse(BaseModel):
    """
    A Pydantic model representing the configuration of the chatbot.
    """
    success: bool
