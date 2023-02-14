import os

from dotenv import load_dotenv
load_dotenv()

# MONGO SETTING
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_HOST", 27017)
MONGO_USER = 'kashyap'
MONGO_PASSWORD = 'Kashyap111$'
MONGO_DB_NAME = 'testing_scrapy_mongo_db'

