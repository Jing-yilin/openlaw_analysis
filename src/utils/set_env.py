"""This package aims to set global env."""
import os

from dotenv import load_dotenv


def set_env():
    """
    To set global env
    """
    # set env
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ['HUGGINGFACE_API_TOKEN'] = os.getenv("HUGGINGFACE_API_TOKEN")
    os.environ["http_proxy"] = os.getenv("http_proxy")
    os.environ["https_proxy"] = os.getenv("https_proxy")
