from bs4 import BeautifulSoup 
import os
import requests
from urllib.parse import urljoin
from link_finder import LinkFinder

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(script_dir, 'myTester.html')

# Read the local HTML file
with open(filename, 'r') as file:
    html_content = file.read()

# Use LinkFinder to extract links from the HTML
base_url = 'file://' + filename
page_url = 'file://' + filename
link_finder = LinkFinder(base_url, page_url)
link_finder.feed(html_content)
found_links = link_finder.page_links()

print("=== LINKS FOUND BY LinkFinder ===")
for link in found_links:
    print(f"  {link}")

# Now fetch and parse each link
print("\n=== FETCHING AND PARSING LINKS ===")
# Limit to first link only for testing
valid_links = [url for url in found_links if url.startswith('http://') or url.startswith('https://')]

if valid_links:
    # Process only the first link
    url = valid_links[0]
    print(f"Processing first link: {url}")
    
    try:
        print(f"\nFetching: {url}")
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("--- STRUCTURED DATA ---")
        # Tables
        tables = soup.find_all('table')
        if tables:
            for i, table in enumerate(tables):
                print(f"Table {i + 1}:")
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    print([col.get_text(strip=True) for col in cols])
        
        # Lists
        lists = soup.find_all('ul')
        if lists:
            print("Lists:")
            for ul in lists:
                items = ul.find_all('li')
                for item in items:
                    print(f"  - {item.get_text(strip=True)}")
        
        print("--- UNSTRUCTURED DATA ---")
        # Headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            print("Headings:")
            for heading in headings[:5]:
                print(f"  {heading.name}: {heading.get_text(strip=True)}")
        
        # First 200 chars of body text
        body_text = soup.get_text(strip=True)
        print(f"Content: {body_text[:200]}...")
        
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
else:
    print("No valid HTTP/HTTPS links found to process")

print(f"\nTotal links found: {len(found_links)}")
print(f"Valid HTTP/HTTPS links: {len(valid_links)}")
if len(valid_links) > 1:
    print(f"Remaining links (not processed): {valid_links[1:]}")

# Also parse the original local file
print("\n\n=== PARSING LOCAL FILE WITH BeautifulSoup ===")
soup = BeautifulSoup(html_content, 'html.parser')

print("=== LINKS IN LOCAL FILE ===")
links = soup.find_all('a')
for link in links:
    href = link.get('href')
    text = link.get_text(strip=True)
    print(f"URL: {href}, Text: {text}")
