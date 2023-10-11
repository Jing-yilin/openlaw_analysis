from langchain.chains import LLMChain
import pathlib
import sys

from .llms import get_llm

sys.path.append(str(pathlib.Path(__file__).resolve().parent))


def get_conversation_chain(
    model_name = "gpt-3.5-turbo-instruct", temperature=0.0, verbose=False, k=2, prompt=None,
):
    """Create a chatgpt chain.

    Args:
        temperature (float): The temperature to use for the language model. Defaults to 0.0.
        verbose (bool): Whether to print the output of the chain. Defaults to True.
        k (int): The number of messages to use for the language model. Defaults to 2.

    Returns:
        ConversationChain: The chatgpt chain.

    Examples:
        >>> from src.chat_model.conversation_chains import get_search_chain
        >>> search_chain = get_search_chain()
        >>> search_chain.predict("Asia Game", "['Chinese (Simplified)', 'English']")
    """

    if prompt is None:
        raise ValueError("Prompt cannot be None.")

    chatgpt_chain = LLMChain(
        llm=get_llm(model_name, temperature),
        prompt=prompt,
        verbose=verbose
    )

    return chatgpt_chain
