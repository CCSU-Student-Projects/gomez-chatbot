
# Use this alongside Mongoshell
# Run this first and check the collection in MongoDB to see the inserted documents. 
from pymongo import MongoClient
import json 

connectionString = "mongodb://localhost:27017/mySecondTestDB"
client = MongoClient(connectionString) 


db = client.get_database("mySecondTestDB")
collection = db.get_collection("secondSetOfDocuments")

with open ("parsed_docs.json", "r", encoding="utf-8") as f:
           for line in f: 
             if line.strip():
                document = json.loads(line) 
                collection.insert_one(document)
print("Done! Documents inserted.")
