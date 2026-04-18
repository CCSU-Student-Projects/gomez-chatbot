from bs4 import BeautifulSoup 
import requests 
from urllib.parse import urlparse 

class HTMLPARSER: 
    
    SKIP_EXTENSIONS = ('.pdf', '.docx', '.doc', '.ppt', '.pptx', 
                       '.xls', '.xlsx', '.zip', '.mp4', '.mp3')
    
    def __init__(self, base_url, domain_name): 
        self.base_url = base_url
        self.domain_name = domain_name
        self.session = requests.Session()  # Use a session for connection pooling and retries
    def parse(self,url): 
        if url.endswith(self.SKIP_EXTENSIONS): # Skip URLs that don't point to HTML content
            print(f"Skipping non-HTML content: {url}")
            return None
        if url.startswith('mailto:') or url.startswith('tel:'):
            print(f"Skipping non-web link: {url}")
            return None
        try: 
            response = self.session.get(url, timeout=10) 
        except Exception as e: 
            print (f"Error fetching {url}: {e}")
            return None
        
        content_type = response.headers.get('Content-Type', '') # Check the Content-Type header to ensure it's HTML
        if 'text/html' not in content_type: 
            print(f"Skipping non-HTML content: {url} (Content-Type: {content_type})")
            return None
    
        soup = BeautifulSoup(response.text, 'html.parser') # Parse the HTML content using BeautifulSoup
        return self.extract_content(soup, url) # Extract structured content from the page
    
    def extract_content(self, soup, url):
        # WE NEED TO REMOVE UNNESSARY CONTENT FOR HTML 
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
            tag.decompose()  # Remove these tags and their content from the soup    

        meta = soup.find('meta', attrs={'name': 'description'})
        
        headings = [
            {
                'level': heading.name,
                'text': heading.get_text(strip=True)
            }
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading.get_text(strip=True)  # Only include headings with non-empty text
        ]
        
        paragraphs = [ 
            text
            for p in soup.find_all('p') 
            if (text := p.get_text(strip=True)) and len(text.split()) > 10
        ]
        return {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'meta_description': meta['content'] if meta and 'content' in meta.attrs else '',
            'headings': headings,
            'paragraphs': paragraphs, 
            'status': 'parsed' 
        }

