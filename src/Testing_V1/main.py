from asyncio import threads
import threading 
import redis 
from queue import Queue 
from spider import Spider
from domain import * 
from fileManager import * 
from urllib.robotparser import RobotFileParser # Added library to fix robots.txt issue 
# Main Information needed to run file! 

PROJECT_NAME = 'CCSU_Crawler'
HOME_PAGE = 'http://ccsu.edu' # Replace link with home page here
DOMAIN_NAME = get_domain_name(HOME_PAGE)
QUEUE_FILE = PROJECT_NAME + '/queue.txt' # Places queue.txt in project folder
CRAWLED_FILE = PROJECT_NAME + '/crawled.txt' # Places crawled.txt in project folder
NUMBER_OF_THREADS = 4 # Starting small for testing

queue = Queue() 


r = redis.Redis(host='localhost', port=6379, db=0) # Connect to Redis server

def load_queue(): 
    links = file_to_set(QUEUE_FILE)
    for link in links:
        if not r.sismember('visited', link): # Check if link is not already crawled
            r.rpush('crawl_queue', link)    
    print(f"{r.llen('crawl_queue')} links loaded into Redis queue") 


Spider(PROJECT_NAME, HOME_PAGE, DOMAIN_NAME) 


# Create worker threads (will die when main exits) 
def create_workers(): 
    threads = [] 
    for _ in range(NUMBER_OF_THREADS):  # _ Is used to indicate looping SOLELY for repetition purposes 
        t = threading.Thread(target = work) 
        t.daemon = True
        t.start() 
        threads.append(t)
    return threads 

# Do the next job in the queue file 
def work(): 
    while True: 
        url = r.lpop('crawl_queue') # Get next link from Redis queue
        if not url: 
            break # Exit if queue is empty 

        url = url.decode('utf-8') # Decode bytes to string
        if r.sismember('visited', url): # Check if link has already been crawled
            continue 
    
        r.sadd('visited',url)
        Spider.crawl_page(threading.current_thread().name, url)


# Check if there are items in the to-do list, if there are, crawl em. 
def crawl(): 
    load_queue() 
    threads = create_workers() 

    for t in threads: 
        t.join() 
   
    print ("Crawl Complete.")
    print(f"Visited: {r.scard('visited')} URLs ")

crawl() 