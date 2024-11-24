from .files import get_absolute_path
from dotenv import load_dotenv as _load_dotenv

def load_dotenv():
    dotenv_path = get_absolute_path(".env")
    _load_dotenv(dotenv_path)
