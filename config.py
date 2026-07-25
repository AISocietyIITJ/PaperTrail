import os
from dotenv import load_dotenv

load_dotenv()

pinecone = os.getenv("PINECONE_API")
