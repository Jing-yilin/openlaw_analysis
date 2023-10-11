"""
chat_model package.
"""

from .conversation_chains import get_conversation_chain
from .llms import get_llm, ALL_MODELS
from .prompts import LAW_RESULT_TEMPLATE

__version__ = "0.1.0"

__all__ = [
    "get_conversation_chain",
    "get_llm",
    "ALL_MODELS",
    "LAW_RESULT_TEMPLATE",
]