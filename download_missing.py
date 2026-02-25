import re
import subprocess
from bs4 import BeautifulSoup
import os

def download_fonts_from_original(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    os.makedirs('fonts', exist_ok=True)
    
    # We will find all colagenotipo2pro.com.br URLs that look like fonts
    urls = set()
    
    # Find in style attributes
    for m in re.finditer(r'url\([\'"]?(https://colagenotipo2pro\.com\.br/[^\'"\)]+\.(?:woff2?|ttf|eot|svg)(?:\?[^\'"\)]*)?)[\'"]?\)', html_content, re.I):
        urls.add(m.group(1))

    for url in urls:
        filename_with_query = url.split('/')[-1]
        filename = filename_with_query.split('?')[0].split('#')[0]
        
        filepath = f'./fonts/{filename}'
        if not os.path.exists(filepath):
            print(f"Downloading {filename} via curl from {url}...")
            try:
                subprocess.run(
                    ['curl.exe', '-H', 'User-Agent: Mozilla/5.0', '-H', 'Accept: */*', '-s', '-o', filepath, url],
                    check=True
                )
            except Exception as e:
                print(f"Failed to download {url}: {e}")

if __name__ == '__main__':
    download_fonts_from_original('index antiga.html')
