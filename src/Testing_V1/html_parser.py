from bs4 import BeautifulSoup 
import requests 
from urllib.parse import urlparse 
import json 
from docling.document_converter import DocumentConverter

converter = None 

def get_Converter(): 
    global converter 
    if converter is None: 
        converter = DocumentConverter() 
    return converter

DOCLING_EXTENSIONS = ('.pdf', '.docx', '.doc', '.ppt', '.pptx', 
                       '.xls', '.xlsx')
SKIP_EXTENSIONS = ('.zip', '.mp4', '.mp3', '.png', '.jpg', '.jpeg')
converter = DocumentConverter() 

class DocumentParser: 
    
    
    def __init__(self, base_url, domain_name): 
        self.base_url = base_url
        self.domain_name = domain_name
        self.session = requests.Session()  # Use a session for connection pooling and retries
    def parse(self,url):  
        try: 
            lower = url.lower() #Set the url to lowercase
            if any(lower.endswith(ext) for ext in SKIP_EXTENSIONS): # ext 
                return None 

            if any(lower.endswith(ext) for ext in DOCLING_EXTENSIONS):
                result = get_Converter().convert(url)
                record = {"url": url, "type": "docling", "content": result.document.export_to_markdown() }
            else: 
                response = self.session.get(url, timeout= 10) 
                soup = BeautifulSoup(response.text, 'html.parser')
                record = self.extract_content(soup, url) 
                record["type"] = "html"

            with open("parsed_docs.jsonl", "a") as f:
                  f.write(json.dumps(record) + "\n")
            return record 
        except Exception as e:
            print(f"Parse error skipping {url}: {e}")
            return None 
    
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
            'type': 'html',
            'title': soup.title.string if soup.title else '',
            'meta_description': meta['content'] if meta and 'content' in meta.attrs else '',
            'headings': headings,
            'paragraphs': paragraphs, 
            'status': 'parsed' 
        }

