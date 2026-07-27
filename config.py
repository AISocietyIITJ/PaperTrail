import os
from dotenv import load_dotenv

load_dotenv()

pinecone = os.getenv("PINECONE_API")
aura_uri = os.getenv("AURA_URI")
aura_user = os.getenv("AURA_USER")
aura_password = os.getenv("AURA_PASSWORD")

