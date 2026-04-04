from urllib.request import urlopen, Request
from link_finder import LinkFinder
from fileManager import * 

class Spider: 
    # Class variables (shared among all instances) 
    project_name = ''
    base_url = ''
    domain_name= ''
    queue_file = ''
    crawled_file = ''
    queue = set() 
    crawled = set() 

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
        Spider.queue = file_to_set(Spider.queue_file)  # When its first created, it won't make multiple 
        Spider.crawled = file_to_set(Spider.crawled_file) 

    @staticmethod 
    def crawl_page(thread_name, page_url): 
        if page_url not in Spider.crawled: 
            print(thread_name + ' now crawling ' + page_url) 
            print('Queue ' + str(len(Spider.queue)) + 
            ' | Crawled: ' + str(len(Spider.crawled)))
            Spider.add_links_to_queue(Spider.gather_links(page_url))
            Spider.queue.remove(page_url)
            Spider.crawled.add(page_url)   
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
            if url in Spider.queue: 
                continue 
            if url in Spider.crawled: 
                continue 
            if Spider.domain_name not in url: 
                continue 
            Spider.queue.add(url) 

    @staticmethod 
    def update_files(): 
        set_to_file(Spider.queue, Spider.queue_file) 
        set_to_file(Spider.crawled,Spider.crawled_file)