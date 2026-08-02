import os
from dotenv import load_dotenv
from pinecone import Pinecone,ServerlessSpec
load_dotenv('keys.env')

pc_api= os.getenv("API_KEY")