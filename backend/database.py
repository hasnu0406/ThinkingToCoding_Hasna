from pymongo import MongoClient

from config import COLLECTION_NAME, DB_NAME, MONGO_URL

mongo_client = MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
resume_collection = db["resumes"]
search_history_collection = db["search_history"]
users_collection = db["users"]
