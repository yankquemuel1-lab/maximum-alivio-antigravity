import re
from bs4 import BeautifulSoup

def apply_layout_fixes(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Fix Anvisa and ReclameAqui Seal align/sizing
    # The user says they are misaligned and one is bigger than the other.
    # To fix this, we can set a fixed height or max-width so they match,
    # and align them in their containers.
    for img in soup.find_all('img'):
        src = img.get('src', '').lower()
        if 'sl_anvisa' in src or 'ra_selo' in src:
            # Add a specific style to force matching scale. E.g. height: 100px; object-fit: contain;
            style = img.get('style', '')
            img['style'] = style + '; height: 90px !important; width: auto !important; object-fit: contain;'
            # Also center it in its container if it isn't already
            parent = img.parent
            if parent and parent.name in ['div', 'figure']:
                parent['style'] = parent.get('style', '') + '; display: flex; justify-content: center; align-items: center;'


    # 2. Add spacing below "EU PRECISO EXPERIMENTAR!" button.
    # Let's find links that navigate to Braip (the checkout buttons) and add margin-bottom
    # Specifically the ones that say "EXPERIMENTAR" or are main CTA buttons.
    for a in soup.find_all('a'):
        href = a.get('href', '')
        text = a.get_text().upper()
        if 'BRAIP.COM' in href.upper() or 'EXPERIMENTAR' in text:
            # We can just add margin wrapper or margin to the button's wrapper
            # Elementor buttons are usually inside a `div.elementor-widget-button`
            wrapper = a.find_parent(class_=re.compile(r'elementor-widget-button'))
            if wrapper:
                ext_style = wrapper.get('style', '')
                wrapper['style'] = ext_style + '; margin-bottom: 30px !important;'
            else:
                ext_style = a.get('style', '')
                a['style'] = ext_style + '; margin-bottom: 30px !important; display: inline-block;'

    # 3. Center align the 30-day guarantee seal, especially on mobile
    # We will target 'garantia.png' which is the main 30 DIAS gold seal.
    # Note: 'pote_garantia.png' might be the bottle image. We only want the seal.
    for img in soup.find_all('img'):
        src = img.get('src', '').lower()
        if 'garantia' in src and 'pote' not in src:
            style = img.get('style', '')
            # Force block centering 
            img['style'] = style + '; display: block !important; margin: 0 auto !important; text-align: center;'
            parent = img.parent
            if parent and parent.name in ['div', 'figure']:
                parent['style'] = parent.get('style', '') + '; text-align: center !important; width: 100% !important;'

    # Overwrite the file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("Specific layout fixes applied.")

if __name__ == '__main__':
    apply_layout_fixes('index.html', 'index.html')
