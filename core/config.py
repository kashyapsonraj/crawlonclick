import os
from dotenv import load_dotenv, dotenv_values

# Get the path to the project root (where .env file is located)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, ".env")

# Load environment variables
load_dotenv(env_path)
config = dotenv_values(env_path)

# MONGO SETTING
MONGO_HOST = config.get("MONGO_HOST", "localhost")
MONGO_PORT = config.get("MONGO_PORT", "27017")
MONGO_USER = config.get("MONGO_USER")
MONGO_PASSWORD = config.get("MONGO_PASSWORD")
MONGO_DB_NAME = config.get("MONGO_DB_NAME", "default_db")
