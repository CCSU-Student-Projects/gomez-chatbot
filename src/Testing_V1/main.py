import threading
import time
import redis
from spider import Spider
from domain import *
from fileManager import *


# Redis commands used:
# r.sismember(key, member) - Check if member (url) exists in set
# r.rpush(key, value) - Push value to end of list
# r.llen(key) - Get length of list
# r.lpop(key) - Pop value from start of list
# r.sadd(key, member) - Add member to set
# r.flushdb() - Clear all keys in current queue 
# r.scard(key) - Get cardinality (size) of set

# Configuration

# NOTE: Docker Desktop must be installed and running for this to work, and Redis must be set up as well! 

PROJECT_NAME = 'CCSU_Crawl_Test' 
HOME_PAGE = 'https://www.ccsu.edu/a-z-index'
DOMAIN_NAME = get_domain_name(HOME_PAGE)
QUEUE_FILE = PROJECT_NAME + '/queue.txt'
CRAWLED_FILE = PROJECT_NAME + '/crawled.txt'
NUMBER_OF_THREADS = 4

# Initialize Redis connection (Connects to local Redis instance)
r = redis.Redis(host='localhost', port=6379, db=0)


# Load initial URLs from queue.txt into Redis
def load_queue():
    links = file_to_set(QUEUE_FILE)
    for link in links:
        if not r.sismember('visited', link):  # Only add to queue if not already visited
            r.rpush('crawl_queue', link)
    print(f"{r.llen('crawl_queue')} links loaded into Redis queue") #Print the number of links loaded into Redis 

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
        url = r.lpop('crawl_queue') # Get a URL from the Redis queue
        if not url:
            time.sleep(0.5) ### If the queue is empty, you need to wait for a bit before trying again to avoid busy-waiting ### 
            continue
        url = url.decode('utf-8') # Decode bytes to string
        if r.sismember('visited', url):
            continue
        r.sadd('visited', url) # Mark URL as visited in Redis
        Spider.crawl_page(threading.current_thread().name, url)

def crawl():
    r.flushdb() # Clear Redis for a fresh start
    Spider(PROJECT_NAME, HOME_PAGE, DOMAIN_NAME)  # Explores queue.txt first
    r.rpush('crawl_queue',HOME_PAGE)
    Spider.crawl_page('Main', HOME_PAGE)

    print(f"Starting with the homepage, found {r.llen('crawl_queue')} links in the queue.")
    create_workers()
    empty_count = 0 
    while empty_count < 5:  # Wait until the queue is empty for a few checks
        if r.llen('crawl_queue') == 0:
            empty_count += 1
            # Count for up to five seconds of an empty queue before concluding the crawl is complete
            print(f"Queue is empty... {empty_count} /5") 
        else:
            empty_count = 0
            print(f"Initial Queue Size: {r.llen('crawl_queue')}") 
        time.sleep(2)

    print("Crawl Complete.") 
    print(f"Total Unique URLs Visited: {r.scard('visited')} URLs") # Print the total number of unique URLs visited

crawl()