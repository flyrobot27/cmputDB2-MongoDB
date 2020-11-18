#import pymongo
from pymongo import MongoClient
import json
import datetime

# Connect to the default port on localhost for the mongodb server.
client = MongoClient("mongodb://127.0.0.1:27012")

# Create or open the store database on server.
db = client["store"]

# List collection names.
#collist = db.list_collection_name()

# Create or open the collection in the db
tags_collection = db["tags_collection"]
votes_collection = db["votes_collection"]
posts_collection = db["posts_collection"]

# delete all previous entries. specify no condition.
tags_collection.delete_many({})
votes_collection.delete_many({})
posts_collection.delete_many({})

#testing
with open('/Users/nati/Downloads/Tags.json') as Tags:
    Tags_data = json.load(Tags)
tags_collection.insert_one(Tags_data)
with open('/Users/nati/Downloads/Votes.json') as Votes:
    Votes_data = json.load(Votes)
votes_collection.insert_one(Votes_data)
with open('/Users/nati/Downloads/Posts.json') as Posts:
    Posts_data = json.load(Posts)
posts_collection.insert_one(Posts_data)

print(Tags_data)
