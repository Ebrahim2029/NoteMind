from dotenv import load_dotenv
import os

from utils.chunker.download_data import ensure_punkt

def reload_env():
    load_dotenv(override=False)

class App_Settings:
    def __init__(self):
        
        reload_env()
        # PostgreSQL
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
        self.POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', 'smart_notes')
        self.POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

        # Redis
        self.REDIS_HOST = os.getenv('REDIS_HOST','redis')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.REDIS_DB = int(os.getenv('REDIS_DB', 0))
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD') or None

        # Chroma
        self.CHROMA_HTTP_URL = os.getenv('CHROMA_HTTP_URL')           # e.g., http://localhost:8000
        self.CHROMA_NAME_DATABASE = os.getenv('CHROMA_NAME_DATABASE', 'notes_db')
        self.RETRIEVAL_THRESHOLD = float(os.getenv('RETRIEVAL_THRESHOLD', 0.7))
        #CHROMA_COLLECTION = os.getenv('CHROMA_COLLECTION', 'notes')
        #CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR')     # for local duckdb+parquet

        # OpenAI
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.OPENAI_EMBED_MODEL = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
        # JWT
        self.JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret')
        self.JWT_ALG = os.getenv('JWT_ALG', 'HS256')
        self.JWT_EXP_MINUTES = int(os.getenv('JWT_EXP_MINUTES', 60))
        # General
        self.APP_ENV = os.getenv('APP_ENV', 'development')
        self.APP_DEBUG = os.getenv('APP_DEBUG', 'True').lower() in ('true', '1', 'yes')

    

app_settings = App_Settings()

