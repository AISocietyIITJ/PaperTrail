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
    with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f) or {}
except Exception:
    yaml_config = {}

neo_conf = yaml_config.get("neo4j", {})

# Expose API Keys & Secrets uniformly with fallback to config.yaml
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") or os.getenv("PINECONE_API") or os.getenv("API_KEY")
AURA_URI = os.getenv("AURA_URI") or os.getenv("NEO4J_URI") or neo_conf.get("uri", "bolt://127.0.0.1:7687")
AURA_USER = os.getenv("AURA_USER") or os.getenv("NEO4J_USER") or neo_conf.get("user", "neo4j")
AURA_PASSWORD = os.getenv("AURA_PASSWORD") or os.getenv("NEO4J_PASSWORD") or neo_conf.get("password", "")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
