from python.helpers.dotenv import load_dotenv
import os
from langchain_community.llms.ollama import Ollama
from langchain_ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_groq import ChatGroq


load_dotenv()

DEFAULT_TEMPERATURE = 0.0

def get_api_key(service):
    return os.getenv(f"API_KEY_{service.upper()}") or os.getenv(f"{service.upper()}_API_KEY")

def get_ollama_chat(
        model_name:str, 
        temperature=DEFAULT_TEMPERATURE, 
        base_url=os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434", num_ctx=8192
    ):
    return ChatOllama(model=model_name,
            temperature=temperature,
            base_url=base_url,
            num_ctx=num_ctx,
    )

def get_ollama_embedding(
        model_name:str, 
        temperature=DEFAULT_TEMPERATURE, 
        base_url=os.getenv("OLLAMA_BASE_URL") or "http://127.0.0.1:11434"
    ):
    return OllamaEmbeddings(model=model_name,
            temperature=temperature,
            base_url=base_url)


def get_groq_chat(
        model_name: str,
        api_key=get_api_key("groq"),
        temperature=DEFAULT_TEMPERATURE,
        #max_tokens = None,
        #timeout = None,
        #max_retries = 2,
    ):
    return ChatGroq(model=model_name,
            temperature=temperature,
            #max_tokens=max_tokens,
            #timeout=timeout,
            api_key=api_key,
            #max_retries=max_retries,
    )


