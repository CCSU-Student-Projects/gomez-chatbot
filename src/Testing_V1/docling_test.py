from docling.document_converter import DocumentConverter
from html_parser import * 
import redis
# Initialize the converter
'''
converter = DocumentConverter()

# Convert a document (from a local path, URL, or stream)
result = converter.convert(source)

# Export the result to Markdown
print(result.document.export_to_markdown())   
'''

# This class calls the Redis file, and prints the queued documents in Redis. 
# NOTE: This is for any DOCLING documents that are queued in Redis. It will print the URLs of the documents that are currently in the queue.

r = redis.Redis(host='localhost', port=6379, db=0)
docs = [u.decode('utf-8') for u in r.lrange('doc_queue', 0, -1)]
print(f"Docs queued: {docs} | Total: {len(docs)}")