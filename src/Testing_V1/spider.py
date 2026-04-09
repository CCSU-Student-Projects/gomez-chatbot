from urllib.request import urlopen, Request
from link_finder import LinkFinder
from fileManager import * 
import redis 

r = redis.Redis(host='localhost', port=6379, db=0) # Connect to Redis server

class Spider: 
    # Class variables (shared among all instances) 
    project_name = ''
    base_url = ''
    domain_name= ''
    queue_file = ''
    crawled_file = ''


    def __init__(self, project_name, base_url, domain_name): 
        Spider.project_name = project_name 
        Spider.base_url = base_url
        Spider.domain_name = domain_name
        Spider.queue_file = Spider.project_name + '/queue.txt'
        Spider.crawled_file = Spider.project_name + '/crawled.txt'
        self.bootUP() 
        self.crawl_page('First spider', Spider.base_url) 
    @staticmethod
    def bootUP(): 
        create_project_dir(Spider.project_name) 
        create_data_files(Spider.project_name, Spider.base_url)
        
        for url in file_to_set(Spider.queue_file):
            if not r.sismember('visited', url): # Check if link is not already crawled
                r.rpush('crawl_queue', url)

        for url in file_to_set(Spider.crawled_file):
                    r.sadd('visited', url)
    @staticmethod 
    def crawl_page(thread_name, page_url): 
            if not r.sismember('visited', page_url):
                print (thread_name + ' now crawling ' + page_url) 
                print ('Queue' + str(r.llen('crawl_queue')) + ''
                ' | Crawled: ' + str(r.scard('visited')))
                Spider.add_links_to_queue(Spider.gather_links(page_url))
                r.lrem('crawl_queue', 1, page_url) # Remove the URL from the Redis queue
                r.sadd('visited', page_url)
                Spider.update_files() 

    @staticmethod 
    def gather_links(page_url):
        html_string = '' 
        try: 
            req = Request(page_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            response = urlopen(req) 
            content_type = response.getheader('Content-Type')
            if content_type and 'text/html' in content_type: 
                html_bytes = response.read() 
                html_string = html_bytes.decode("utf-8", errors='ignore')
            else:
                return set()
            finder = LinkFinder(Spider.base_url, page_url)
            finder.feed(html_string) 
        except Exception as e: 
            print('Error: Cannot crawl page', page_url, e)
            return set() 
        return finder.page_links()
    
    @staticmethod 
    def add_links_to_queue(links): # Loop through each link one by one, if it exists, go to the next item in the list 
        for url in links: 
            if r.sismember('visited', url) or r.sismember('queued', url): 
                continue 
            if Spider.domain_name not in url:
                continue 
            r.rpush('crawl_queue', url) # Add the URL to the Redis queue    
            r.sadd('queued', url) # Add the URL to the Redis set of queued URLs
           
    @staticmethod 
    def update_files(): 
        queue = r.lrange('crawl_queue', 0, -1) # Get all URLs in the Redis queue
        set_to_file({u.decode('utf-8') for u in queue}, Spider.queue_file) # Save the queue to file
        visited = r.smembers('visited') # Get all visited URLs from Redis set
        set_to_file({u.decode('utf-8') for u in visited}, Spider.crawled_file) # Save the visited URLs to file