from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import DATABASE_NAME, MONGO_URI

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

database = client[DATABASE_NAME]
users_collection = database["users"]


def check_database_connection() -> bool:
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False