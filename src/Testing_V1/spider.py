import json
from urllib.request import urlopen, Request
from urllib.robotparser import RobotFileParser
from link_finder import LinkFinder
from urllib.parse import urlparse
from fileManager import * 
from html_parser import * 
from docling_test import convert_pdfs_to_json
import redis 
import threading

r = redis.Redis(host='localhost', port=6379, db=0) # Connect to Redis server

class Spider: 
    # Class variables (shared among all instances to prevent overlapping data)
    project_name = ''
    base_url = ''
    domain_name= ''
    queue_file = ''
    crawled_file = ''
    parser = None
    parsed_docs = [] 
    lock = threading.Lock() # Preventing multiple workers accessing the same URL 
    BLOCKED_URLS = ['library.ccsu.edu', 'libguides.ccsu.edu', 'ccsu.edu/bookings'] # An example of a domain to block (can be expanded as needed)

# Spider class to manage crawling and link extraction
    def __init__(self, project_name, base_url, domain_name): 
        Spider.project_name = project_name 
        Spider.base_url = base_url
        Spider.domain_name = domain_name
        Spider.queue_file = Spider.project_name + '/queue.txt'
        Spider.crawled_file = Spider.project_name + '/crawled.txt'
        self.bootUP() 

    @staticmethod
    # Robot Parser to check if crawling is allowed for a URL
    def get_robot_parser():
        if not hasattr(Spider, '_robot_parser'):
            Spider._robot_parser = RobotFileParser()
            Spider._robot_parser.set_url(f"{Spider.base_url}/robots.txt")
            Spider._robot_parser.read()
        return Spider._robot_parser
    @staticmethod
    def bootUP(): 
        r.flushdb() 
        create_project_dir(Spider.project_name) 
        create_data_files(Spider.project_name, Spider.base_url)
        Spider.parser = DocumentParser(Spider.base_url, Spider.domain_name)
        # Initialize and cache the robot parser once
        Spider.get_robot_parser()
# Static method to crawl a page and extract links
    @staticmethod 
    def crawl_page(thread_name, page_url): 
            print(f"{thread_name} crawling: {page_url}")
            links = Spider.gather_links_smart(page_url) 
            Spider.add_links_to_queue(links) # Add the new links to the Redis queue
            
            if Spider.parser: 
                doc = Spider.parser.parse(page_url)
                if doc: 
                    with  Spider.lock: 
                        Spider.parsed_docs.append(doc)
                        if len(Spider.parsed_docs) >= 10: # Every 10 parsed documents, save to file to prevent memory loss 
                            with open(f"{Spider.project_name}/parsed_docs.jsonl", 'a', encoding='utf-8') as f:
                                for document in Spider.parsed_docs:
                                    f.write(json.dumps(document, ensure_ascii=False) + '\n')
                                Spider.parsed_docs.clear()
                                print("--- SAVED BATCHES TO JSONL ---") 

                Spider.update_files()  # Update the queue and crawled files from Redis data

    @staticmethod 
    # Static method to gather links from a page
    def gather_links(page_url):
        if not Spider.get_robot_parser().can_fetch("*", page_url):
            print(f"Blocked by robots.txt: {page_url}")
            return set()
        
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
    
    '''
    @staticmethod 
    # Static method to gather links from a page using Playwright for JS rendering
    def gather_links_with_js(page_url):
        """Gather links from JS-rendered pages using Playwright"""
        html_string = ''
        try:
            from playwright.sync_api import sync_playwright # Importing here to avoid dependency if not using JS crawling
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_viewport_size({"width": 1280, "height": 720})
                
                # Navigate to the page and wait for network to settle
                page.goto(page_url, wait_until="networkidle", timeout=30000)
                
                # Wait a bit for any dynamic content to load
                page.wait_for_timeout(2000)
                
                # Get the rendered HTML
                html_string = page.content()
                browser.close()
                
            finder = LinkFinder(Spider.base_url, page_url)
            finder.feed(html_string)
            
        except Exception as e:
            print(f'Error: Cannot crawl page with Playwright {page_url}: {e}')
            return set()
        
        return finder.page_links()
'''
    @staticmethod 
    # Static method to gather links from a page (tries regular method first, then JS if needed)
    def gather_links_smart(page_url):
        """Try regular crawling first, fallback to Playwright for JS-heavy pages"""
        links = Spider.gather_links(page_url)
    
        return links

    ''''
        # If we got very few links, try with Playwright (might be JS-rendered)
        if len(links) < 5:
            print(f'  → Low link count ({len(links)}), trying Playwright for JS-rendered content...')
            js_links = Spider.gather_links_with_js(page_url)
            if len(js_links) > len(links):
                print(f'  → Playwright found {len(js_links)} links (vs {len(links)} before)')
                return js_links
    '''


    @staticmethod 
    def add_links_to_queue(links): # Loop through each link one by one, if it exists, go to the next item in the list 
        for url in links: 
            if any (blocked in url for blocked in Spider.BLOCKED_URLS):
                continue
            if url.startswith(('mailto:', 'tel:', 'javascript:', 'Mailto:', '#')): 
                continue
            if Spider.domain_name not in url:
                continue 
            if any (url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
                continue
            parsed = urlparse(url)
            if not Spider.get_robot_parser().can_fetch("*", url):
                continue 
            if not r.sismember('visited', url) and r.sadd('queued', url): # Only add to queue if not already visited or queued
                if any(url.lower().endswith(ext) for ext in DOCLING_EXTENSIONS): 
                    r.rpush('doc_queue', url) # BASICALLY ONLY DO DOCLING AFTER IT RUNS THE OTHERS 
                else: 
                    r.rpush('waitingRoom_queue', url)
                
    @staticmethod 
    # Static method to update the queue and crawled files from Redis data
    def update_files(): 
        queue = r.lrange('waitingRoom_queue', 0, -1) # Get all URLs in the Redis queue
        set_to_file({u.decode('utf-8') for u in queue}, Spider.queue_file) # Save the queue to file
        visited = r.smembers('visited') # Get all visited URLs from Redis set
        set_to_file({u.decode('utf-8') for u in visited}, Spider.crawled_file) # Save the visited URLs to file

