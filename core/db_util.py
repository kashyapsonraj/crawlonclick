from . import config, logger
from pymongo import MongoClient


class MongoDBUtil:
    """
    Mongo DB Util.
    """

    @classmethod
    def get_conn(cls):
        username = config.MONGO_USER
        password = config.MONGO_PASSWORD
        conn_string = "mongodb+srv://%s:%s@cluster0.d82qhej.mongodb.net/?retryWrites=true&w=majority" % (username, password)
        return MongoClient(conn_string)
