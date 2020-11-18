import pymongo
from pymongo import MongoClient
import datetime

# Connect to the default port on localhost for the mongodb server.
client = MongoClient()

# Create or open the store database on server.
db = client["store"]

# List collection names.
collist = db.list_collection_name()

# Create or open the collection in the db
tags_collection = db["tags_collection"]
votes_collection = db["votes_collection"]
posts_collection = db["posts_collection"]

# delete all previous entries. specify no condition.
tags_collection.delete_many({})
votes_collection.delete_many({})
posts_collection.delete_many({})

mo = tags_collection.insert_many(Tags.json)
more = mo.inserted_ids
print(more)
