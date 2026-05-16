
from html_parser import * 
import redis
import json

from docling.document_converter import DocumentConverter

# This class calls the Redis file, and prints the queued documents in Redis. 
# NOTE: This is for any DOCLING documents that are queued in Redis. It will print the URLs of the documents that are currently in the queue.

r = redis.Redis(host='localhost', port=6380 , db=0)
docs = [u.decode('utf-8') for u in r.lrange('docling_queue', 0, -1)]
print(f"Docs queued: {docs} | Total: {len(docs)}")
    #https://www.docling.ai/#start """

def convert_pdfs_to_json(urls, output_file="docling_output.json"):
    converter = DocumentConverter()
    results = []

    for url in urls:
        try:
            print(f"Processing: {url}")
            doc = converter.convert(url).document
            
            # Extract content
            markdown = doc.export_to_markdown()

            results.append({
                "source": url,
                "content": markdown
            })

        except Exception as e:
            print(f"Error processing {url}: {e}")
            results.append({
                "source": url,
                "error": str(e)
            })

    # Save to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Saved results to {output_file}")


