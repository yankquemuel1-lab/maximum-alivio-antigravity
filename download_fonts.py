import re
import subprocess
from bs4 import BeautifulSoup
import os

def fix_fonts_and_align(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    os.makedirs('fonts', exist_ok=True)
    
    def download_and_replace_font(m):
        full_url = m.group(1).strip('"\'')
        
        if 'colagenotipo2pro.com.br' in full_url and re.search(r'\.(woff2?|ttf|eot|svg)(\?.*)?$', full_url, re.I):
            filename_with_query = full_url.split('/')[-1]
            filename = filename_with_query.split('?')[0]
            
            if not os.path.exists(f'./fonts/{filename}'):
                print(f"Downloading {filename} via curl...")
                try:
                    subprocess.run(
                        ['curl.exe', '-H', 'User-Agent: Mozilla/5.0', '-H', 'Accept: */*', '-s', '-o', f'./fonts/{filename}', full_url],
                        check=True
                    )
                except Exception as e:
                    print(f"Failed to download {full_url}: {e}")
            
            return f'url(./fonts/{filename})'
        return m.group(0)

    for tag in soup.find_all(style=True):
        style = tag['style']
        if 'url(' in style:
            tag['style'] = re.sub(r'url\((.*?)\)', download_and_replace_font, style)

    for style_tag in soup.find_all('style'):
        if style_tag.string:
            new_css = re.sub(r'url\((.*?)\)', download_and_replace_font, style_tag.string)
            def fix_css_img(m):
                url = m.group(1).strip('"\'')
                if 'colagenotipo2pro.com.br' in url and re.search(r'\.(jpg|jpeg|png|webp|gif)$', url, re.I):
                    fname = url.split('/')[-1].split('?')[0]
                    return f'url(./images/{fname})'
                return m.group(0)
            
            new_css = re.sub(r'url\((.*?)\)', fix_css_img, new_css)
            style_tag.string.replace_with(new_css)

    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'garantia' in src.lower() or 'selo' in src.lower() or '30' in src.lower():
            p_style = img.parent.get('style', '') if img.parent else ''
            print(f"Centering seal image: {src}")
            img['style'] = img.get('style', '') + '; display: block; margin: 0 auto;'
            if img.parent and img.parent.name in ['div', 'figure']:
                img.parent['style'] = p_style + '; text-align: center; width: 100%; display: flex; justify-content: center;'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("Fonts downloaded and CSS/images aligned.")

if __name__ == '__main__':
    fix_fonts_and_align('index.html', 'index.html')
