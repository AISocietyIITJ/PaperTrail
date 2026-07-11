import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    USERNAME:str = os.getenv("USERNAME","")
    PASSWORD:str = os.getenv("PASSWORD","")



settings = Config()
