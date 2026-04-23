import threading
import time
import redis
from spider import Spider
from domain import *
from fileManager import *
import json 


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

PROJECT_NAME = 'CCSU_Crawl_Test' 
HOME_PAGE = 'https://www.ccsu.edu/a-z-index'
DOMAIN_NAME = 'ccsu.edu'
NUMBER_OF_THREADS = 8
# Initialize Redis connection (Connects to local Redis instance)
r = redis.Redis(host='localhost', port=6379, db=0)


# Load initial URLs from queue.txt into Redis

def load_queue():
    links = file_to_set('queue.txt')
    for link in links:
        if not r.sismember('visited', link):  # Only add to queue if not already visited
            r.rpush('crawl_queue', link)
    print(f"{r.llen('crawl_queue')} links loaded into Redis queue") # Print the number of links loaded into Redis 

def create_workers():
    threads = [] # Create worker threads to process the crawl queue
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work) 
        t.daemon = True
        t.start()
        threads.append(t)
    return threads

# Worker function to process URLs from the Redis queue
def work():
    
    while True:
        # Get a URL and wait 5 seconds. 
        result = r.blpop('crawl_queue', timeout=5) # Get a URL from the Redis queue
        if not result:  # If no URL is retrieved within the timeout, break the loop
            continue 
        url = result[1].decode('utf-8')  # Decode bytes to string

        if r.sadd('visited' , url): # Mark the URL as visited in Redis
            Spider.crawl_page(threading.current_thread().name, url) # Crawl the page and extract links


def crawl():
    r.flushdb() # Clear Redis for a fresh start 
    print("Starting crawl...")
    Spider(PROJECT_NAME, HOME_PAGE, DOMAIN_NAME)  
    # Explores queue.txt first
    r.rpush('crawl_queue',HOME_PAGE)
    Spider.crawl_page('Main', HOME_PAGE)

    create_workers() # Start worker threads to process the crawl queue

    while True: 
        queue_size = r.llen('crawl_queue')
        print(f"Queue Size: {r.llen('crawl_queue')} | Visited: {r.scard('visited')} ")
        if queue_size == 100: 
            break
        time.sleep(5)

# Flush any remaining docs under 100
        if Spider.parsed_docs:
            with open(PROJECT_NAME + '/parsed_docs.json', 'a', encoding='utf-8') as f:
                for d in Spider.parsed_docs:
                     f.write(json.dumps(d, ensure_ascii=False) + '\n')
        print("Crawl complete! Final stats:")
        print(f"Total URLs visited: {r.scard('visited')}")

if __name__ == '__main__':
      crawl() 
