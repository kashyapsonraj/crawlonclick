import os

from dotenv import load_dotenv
load_dotenv()

# MONGO SETTING
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_HOST")
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
