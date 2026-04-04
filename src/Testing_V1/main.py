import threading 
from queue import Queue 
from spider import Spider
from domain import * 
from fileManager import * 
from urllib.robotparser import RobotFileParser # Added library to fix robots.txt issue 
# Main Information needed to run file! 

PROJECT_NAME = 'CCSU'
HOME_PAGE = 'https://www.ccsu.edu/' # Replace link with home page here
DOMAIN_NAME = get_domain_name(HOME_PAGE)
QUEUE_FILE = PROJECT_NAME + '/queue.txt'
CRAWLED_FILE = PROJECT_NAME + '/crawled.txt'
NUMBER_OF_THREADS = 2 # Starting small for testing

queue = Queue() 

Spider(PROJECT_NAME, HOME_PAGE, DOMAIN_NAME) 

# Create worker threads (will die when main exits) 
def create_workers(): 
    for _ in range(NUMBER_OF_THREADS):  # _ Is used to indicate looping SOLELY for repetition purposes 
        t = threading.Thread(target = work) 
        t.daemon = True
        t.start() 

# Do the next job in the queue file 
def work(): 
    while True: 
        url = queue.get() 
        Spider.crawl_page(threading.current_thread().name, url)
        queue.task_done() 


# Check if there are items in the to-do list, if there are, crawl em. 
def crawl(): 
    queue_links = file_to_set(QUEUE_FILE) 
    if len(queue_links) > 0: 
        print(str(len(queue_links)) + 'links in the queue')
        create_jobs()

# Each queued link is a new job 
def create_jobs(): 
    for link in file_to_set(QUEUE_FILE): 
        queue.put(link) 
    queue.join() 
    crawl() 

create_workers() 
crawl() 