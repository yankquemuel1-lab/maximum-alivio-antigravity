import re

def replace_absolute_fonts_with_cdns(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        html = f.read()

    def replacer(m):
        full_url = m.group(1)
        # Extract filename
        filename_with_query = full_url.split('/')[-1]
        filename = filename_with_query.split('?')[0].split('#')[0]
        name_no_ext = filename.split('.')[0]
        ext = filename.split('.')[-1]
        
        # We only want to replace font files from this specific domain
        if ext in ['woff2', 'woff', 'ttf', 'eot', 'svg']:
            if 'fa-solid' in name_no_ext:
                return f'url(https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/{filename})'
            elif 'fa-regular' in name_no_ext:
                return f'url(https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/{filename})'
            elif 'fa-brands' in name_no_ext:
                return f'url(https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/{filename})'
            elif 'eicons' in name_no_ext:
                return f'url(https://cdn.jsdelivr.net/gh/elementor/elementor@3.27.0/assets/lib/eicons/fonts/{filename})'
        
        return m.group(0)

    # Search for url(https://colagenotipo2pro.com.br/...)
    html = re.sub(r'url\([\'"]?(https://colagenotipo2pro\.com\.br/[^\'"\)]+\.(?:woff2?|ttf|eot|svg)(?:\?[^\'"\)]*)?)[\'"]?\)', replacer, html)

    # Also fix the img.src JS snippet if any
    html = html.replace("img.src = 'https://colagenotipo2pro.com.br/wp-content/uploads/2023/11/img_principal_fundo.png';", "img.src = './images/img_principal_fundo.png';")

    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Replaced producer font URLs with CDNs.")

if __name__ == '__main__':
    replace_absolute_fonts_with_cdns('index.html')
