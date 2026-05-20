import redis
import json
from docling.document_converter import DocumentConverter

# Connect to the same Redis instance your spider uses 
r = redis.Redis(host='localhost', port=6379, db=0)
converter = DocumentConverter()

def process_documents(project_name):
    print("Docling Processor started. Waiting for documents...")
    
    while True:
        # This "pops" a URL from the 'doc_queue' created by your spider 
        _, url_bytes = r.blpop('doc_queue')
        url = url_bytes.decode('utf-8')
        
        try:
            print(f"Converting: {url}")
            result = converter.convert(url)
            markdown_content = result.document.export_to_markdown() # Removed the cite code here 
            
            # Print the output to your console
            print(f"\n--- CONVERSION SUCCESSFUL: {url} ---")
            print(markdown_content[:1000]) # Print first 1000 chars
            print("-" * 50)
            
            # Optionally save to a separate file
            with open(f"{project_name}/converted_docs.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"url": url, "content": markdown_content}) + "\n")
                
        except Exception as e:
            print(f"Failed to convert {url}: {e}")

if __name__ == "__main__":
    process_documents("CCSU_Crawl_HTML_DOCLING_TEST")