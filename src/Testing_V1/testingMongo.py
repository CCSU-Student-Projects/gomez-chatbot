
# Use this alongside Mongoshell
# Run this first and check the collection in MongoDB to see the inserted documents. 
from pymongo import MongoClient
import json 

connectionString = "mongodb://localhost:27017/website_crawl"
client = MongoClient(connectionString) 


db = client.get_database("website_crawl")
collection = db.get_collection("documents")
collection.delete_many({})  # wipe before inserting

with open ("CCSU_Crawl_Test/parsed_docs.jsonl", "r", encoding="utf-8") as f:
           for line in f: 
             if line.strip():
                document = json.loads(line) 
                collection.insert_one(document)
      
print("Done! Documents inserted.")
