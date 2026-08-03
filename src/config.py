import os
from dotenv import load_dotenv
import yaml
from pathlib import Path

# Load environment variables from .env
load_dotenv()

# Root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load YAML Config
CONFIG_YAML_PATH = ROOT_DIR / "config.yaml"
try:
    with open(CONFIG_YAML_PATH, "r") as f:
        yaml_config = yaml.safe_load(f)
except FileNotFoundError:
    yaml_config = {}

# Expose API Keys & Secrets uniformly
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or os.getenv("PINECONE_API") or os.getenv("API_KEY")
AURA_URI = os.getenv("AURA_URI")
AURA_USER = os.getenv("AURA_USER")
AURA_PASSWORD = os.getenv("AURA_PASSWORD")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
