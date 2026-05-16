
# Use this alongside Mongoshell
# Run this first and check the collection in MongoDB to see the inserted documents. 

# MongoDB Shell Commands:
# show dbs                                    - List all databases
# use <database_name>                         - Switch to a database
# cls                                         - Clear screen
# show collections                            - List all collections in database
# db.collection.find()                        - Show all documents in collection
# db.collection.find().pretty()               - Show documents formatted
# db.collection.insertOne({})                 - Insert a single document
# db.collection.insertMany([{}])              - Insert multiple documents
# db.collection.deleteOne({})                 - Delete a single document
# db.collection.deleteMany({})               - Delete multiple documents
# db.collection.updateOne({},{$set:{}})       - Update a single document
# db.collection.countDocuments()              - Count documents in collection
# db.dropDatabase()                           - Drop current database
# db.collection.drop()                        - Drop a collection
# exit                                        - Exit MongoDB shell

from pymongo import MongoClient
import json 


connectionString = "mongodb://localhost:27017/website_crawl"
client = MongoClient(connectionString) 
def insert_HTML_Documents_IntoMongoDB(): 
    db = client.get_database("website_crawl")
    collection = db.get_collection("Stored_HTML_URLS")
    with open ("CCSU_Crawl_Test/parsed_docs.jsonl", "r", encoding="utf-8") as f:
           for line in f: 
             if line.strip():
                document = json.loads(line) 
                collection.insert_one(document)
    print("Documents inserted into MongoDB successfully for HTML!")

def insert_Docling_Documents_IntoMongoDB(): 
    db = client.get_database("website_crawl")
    collection = db.get_collection("all_Stored_DOCLING_URLS")
    with open ("CCSU_Crawl_Test/parsed_docs.jsonl", "r", encoding="utf-8") as f:
           for line in f: 
             if line.strip():
                document = json.loads(line) 
                collection.insert_one(document)
    print("Documents inserted into MongoDB successfully for DOCLING!")
