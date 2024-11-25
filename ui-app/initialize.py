import models
from agent import AgentConfig
import os

from python.helpers import files

def initialize():
    model_name = os.getenv("LLM_MODEL_NAME") or "llama2:latest"
    embed_model_name = os.getenv("LLM_EMBED_MODEL_NAME") or "nomic-embed-text"
    #chat_llm = models.get_openai_chat(model_name="gpt-4o-mini", temperature=0)
    #chat_llm = models.get_ollama_chat(model_name="llama3.2:3b-instruct-fp16", temperature=0)
    #chat_llm = models.get_ollama_chat(model_name=model_name, temperature=0)
    chat_llm = models.get_groq_chat(model_name=model_name, temperature = 0)

    utility_llm = chat_llm
    
    embedding_llm = models.get_ollama_embedding(model_name=embed_model_name)

    config = AgentConfig(
            chat_model = chat_llm,
            utility_model = utility_llm,
            embeddings_model = embedding_llm,
            knowledge_subdirs = ["default","custom"],
            auto_memory_count = 0,
            rate_limit_requests = 30,
            max_tool_response_length = 3000,
            code_exec_docker_enabled = True,
            code_exec_ssh_enabled = True,
    )

    return config
