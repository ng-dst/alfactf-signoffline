import os
from pymongo import MongoClient
from flask import Blueprint

# Blueprint
main = Blueprint('main', __name__)

# MongoDB setup
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)

db = client['user_db']
db.users.create_index('username', unique=True)
