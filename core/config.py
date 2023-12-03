from dotenv import load_dotenv
load_dotenv()

from dotenv import dotenv_values
config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}

# MONGO SETTING
MONGO_HOST = config.get("MONGO_HOST")
MONGO_PORT = config.get("MONGO_PORT")
MONGO_USER = config.get("MONGO_USER")
MONGO_PASSWORD = config.get("MONGO_PASSWORD")
MONGO_DB_NAME = config.get("MONGO_DB_NAME")
