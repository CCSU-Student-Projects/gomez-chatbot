import threading
import time
import json 
import redis
from spider import Spider
from domain import *
from fileManager import *
from testingMongo import * 
from pymongo import MongoClient
from docling_test import convert_pdfs_to_json

# Redis commands used:
# r.sismember(key, member) - Check if url exists in set
# r.rpush(key, value) - Push value to end of list
# r.llen(key) - Get length of list
# r.lpop(key) - Pop value from start of list
# r.sadd(key, member) - Add url to set
# r.flushdb() - Clear all keys in current queue 
# r.scard(key) - Get cardinality (size) of set

# Configuration

# NOTE: Docker Desktop must be installed and running for this to work, and Redis must be set up as well! 
# NOTE: MongoDB must be installed and running for this to work as well! 

PROJECT_NAME = 'Test_Crawl' 
HOME_PAGE = 'https://www.ccsu.edu/'
DOMAIN_NAME = 'ccsu.edu'
HTML_THREADS = 12
DOCLING_THREADS = 3
connectionString = "mongodb://localhost:27017/website_crawl"
client = MongoClient(connectionString) 
# Initialize Redis connection (Connects to local Redis instance)
r = redis.Redis(host='localhost', port=6380, db=0)

# Load initial URLs from queue.txt into Redis

def html_parser_worker():
    while True:
        result = r.blpop('waitingRoom_queue', timeout=5)  # Get a URL from the Redis queue
        if not result:  # If no URL is retrieved within the timeout, break the loop
            break 
        url = result[1].decode('utf-8')  # Decode bytes to string

        if r.sadd('visited' , url): # Mark the URL as visited in Redis
            Spider.crawl_page(threading.current_thread().name, url) # Crawl the page and extract links

def docling_worker():
    while True: 
        result = r.blpop('docling_queue', timeout=5) 
        if not result: 
            break
        url = result[1].decode('utf-8')
        if r.sadd('visited', url): 
             print(f"[Docling] Processing: {url}")
             try: 
                convert_pdfs_to_json([url], output_file="docling_output.json")
                print(f"[Docling] Processing: {url}")

             except Exception as e:
                print(f"[Docling] Failed: {url}: {e}")

# Worker function to process URLs from the Redis queue
def work():
    
    while True:
        # Get a URL and wait 5 seconds. 
        result = r.blpop('waitingRoom_queue', timeout=5) # Get a URL from the Redis queue
        if not result:  # If no URL is retrieved within the timeout, break the loop
            continue 
        url = result[1].decode('utf-8')  # Decode bytes to string

        if r.sadd('visited' , url): # Mark the URL as visited in Redis
            Spider.crawl_page(threading.current_thread().name, url) # Crawl the page and extract links

def workOnDocling(): 
     while True: 
        result = r.blpop('docling_queue', timeout=5) 
        if not result: 
            continue 
        url = result[1].decode('utf-8') 
        convert_pdfs_to_json([url], output_file="docling_output.json")

def crawl():
    print("Starting crawl...")
    Spider(PROJECT_NAME, HOME_PAGE, DOMAIN_NAME)  
    # Explores the queue
    r.rpush('waitingRoom_queue',HOME_PAGE)
    Spider.crawl_page('Main', HOME_PAGE)

#################### BEGINNING OF CRAWL ####################


    print(f"\nStarting HTML phase with {HTML_THREADS} threads")
    html_threads = [threading.Thread(target=html_parser_worker, daemon=True) for _ in range(HTML_THREADS)]
    for t in html_threads:
         t.start()

    while any(t.is_alive() for t in html_threads):
        print(f"Queue Size: {r.llen('waitingRoom_queue')} | Visited: {r.scard('visited') } | Docling Queue: {r.llen('docling_queue')}")
        time.sleep(5)  # Wait before printing stats again

    if Spider.parsed_docs:
        with open(PROJECT_NAME + '/parsed_docs.jsonl', 'a', encoding='utf-8') as f:
                for d in Spider.parsed_docs:
                     f.write(json.dumps(d, ensure_ascii=False) + '\n')
        Spider.parsed_docs.clear() # Clear in-memory docs after saving to file

    print(f"\nHTML PHASE DONE. Visited {r.scard('visited')} pages.")
    insert_HTML_Documents_IntoMongoDB() # Insert HTML documents into MongoDB after HTML phase is done

# DOCLING PHASE (after HTML phase is done, we can start processing DOCLING documents in the queue)
    doc_count = r.llen('docling_queue')
    if doc_count == 0: 
        print("No documents found for Docling. All done!")
    else: 
        print(f"\nStarting Docling phase with {DOCLING_THREADS} threads for {doc_count} documents.")
        doc_threads = [threading.Thread(target=docling_worker, daemon=True) for _ in range(DOCLING_THREADS)]
        for t in doc_threads:
            t.start()
        while any(t.is_alive() for t in doc_threads):
            print(f"[Docling] Remaining: {r.llen('docling_queue')}")
            time.sleep(5)  # Wait before printing stats again

        print("\nDOCLING PHASE DONE.")

print("FINISHED! INSERTING INTO MONGODB...")

if __name__ == '__main__':
      crawl() 
