import threading
import time
import json 
import redis
from spider import Spider
from domain import *
from fileManager import *
from docling_test import process_documents
from testingMongo import insertHTMLDocuments, insertDoclingDocuments


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

PROJECT_NAME = 'CCSU_Crawl_FINAL_TEST' 
HOME_PAGE = 'https://www.ccsu.edu/'
DOMAIN_NAME = 'ccsu.edu'
NUMBER_OF_THREADS = 12
#connectionString = "mongodb://localhost:27017/website_crawl"*****************
#client = MongoClient(connectionString) ********************
# Initialize Redis connection (Connects to local Redis instance)
r = redis.Redis(host='localhost', port=6379, db=0)


# Load initial URLs from queue.txt into Redis

def docling_work(): 
    process_documents(PROJECT_NAME) 

def doc_workers() :
     print("Starting doc workers...")
     while True:
         # Get a document and wait 5 seconds.
         result = r.blpop('waitingRoom_docs', timeout=5) # Get a document from the Redis queue
         if not result:  # If no document is retrieved within the timeout, break the loop
             continue
         doc = result[1].decode('utf-8')  # Decode bytes to string
         print(f"Processing document: {doc}")
         try:
             # Process the document
             Spider.parser.parse(doc)
         except Exception as e:
             print(f"Error processing document: {doc}, Error: {e}")

             

def create_workers():
    threads = [] # Create worker threads to process the crawl queue
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work) 
        t.daemon = True
        t.start()
        threads.append(t)

        #Docling workers
    docling_worker = threading.Thread(target=docling_work)
    docling_worker.daemon = True
    docling_worker.start()
    threads.append(docling_worker)
    return threads

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


def crawl():
    r.flushdb() 
    print("Starting crawl...")
    Spider(PROJECT_NAME, HOME_PAGE, DOMAIN_NAME)  
    # Explores the queue
    r.rpush('waitingRoom_queue',HOME_PAGE)
    Spider.crawl_page('Main', HOME_PAGE)

    create_workers() # Start worker threads to process the crawl queue

    while True: 
        queue_size = r.llen('waitingRoom_queue')
        print(f"Queue Size: {r.llen('waitingRoom_queue')} | Visited: {r.scard('visited')} ")
        if queue_size == 0: 
            break
        time.sleep(5)

# Flush any remaining docs in memory to file before exiting, and print final stats. 
    if Spider.parsed_docs:
        with open(PROJECT_NAME + '/parsed_docs.jsonl', 'a', encoding='utf-8') as f:
            for d in Spider.parsed_docs:
                    f.write(json.dumps(d, ensure_ascii=False) + '\n')
    print("Crawl complete! Final stats:")
    print(f"Total URLs visited: {r.scard('visited')}")
    insertHTMLDocuments(PROJECT_NAME)
    insertDoclingDocuments(PROJECT_NAME)
if __name__ == '__main__':
      crawl() 
