import re
import urllib.parse
from bs4 import BeautifulSoup

def sanitize_html(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Remove specific scripts, inline scripts with WP globals, and keep essential Elementor
    scripts = soup.find_all('script')
    for script in scripts:
        src = script.get('src', '')
        content = script.string or ''
        
        # Remove refresh.js
        if 'refresh.js' in src:
            script.decompose()
            continue
            
        # Remove exact wp-includes scripts that look unnecessary or load specific wp vars
        if 'wp-includes' in src and not ('jquery' in src.lower()):
            # Keep jQuery if it comes from WP, but actually we already use cdnjs/code.jquery.com 
            # so we can just drop any wp-includes script safely except for essentials
            script.decompose()
            continue
            
        # Remove any scripts from colagenotipo2pro.com.br unless it's an essential elementor script
        # Wait, the user said keep essential Elementor JS.
        # Elementor scripts are usually in wp-content/plugins/elementor/assets/js/
        # Let's remove anything that is not elementor. Wait, even better, if we keep elementor, it points to the producer's domain.
        # Elementor scripts might cause CORS or 404 if we are not hosting them.
        # Actually, let's keep elementor scripts but change the domain? No, we don't have those JS files locally.
        # If we keep them pointing to the producer domain, they might work or fail. The user said:
        # "Cuidado ao remover todos os scripts do Elementor... Peça ao Antigravity para manter apenas o CSS essencial e os scripts de animação básicos, mas limpando todas as chamadas externas e variáveis globais do WordPress"
        # Since we don't have the JS files, keeping the `<script src="https://colagenotipo2pro.com.br/.../elementor/...js">` 
        # is the only way unless we download them. The user only said images are downloaded locally.
        # Let's leave src as is for elementor scripts, but remove inline WP variables.
        
        if 'wp.i18n' in content or 'wp-i18n' in content:
            script.decompose()
            continue
            
        if 'elementorFrontendConfig' in content or 'ElementorProFrontendConfig' in content:
            # We can strip out the problematic parts or remove it entirely. But elementor might crash without config.
            # Usually elementor frontend config sets up URLs. Let's try to remove it, or just leave it but strip the api keys?
            # User specifically said: "limpando todas as chamadas externas e variáveis globais do WordPress que geram erros"
            # Actually, the user's prompt originally said: "Remova todos os scripts e variáveis de WordPress (wp-i18n, wp-, etc.) e Elementor que geram erros de 'ReferenceError'"
            # If elementorFrontendConfig generates ReferenceError, it's often because jQuery or `elementorFrontend` isn't loaded right, or it references missing variables.
            # Let's remove elementorFrontendConfig entirely.
            script.decompose()
            continue
            
        # Remove Meta CAPI block
        if '/api/meta-event' in content:
            script.decompose()
            continue

        if 'window.dataLayer' in content and 'gtag' in content:
            # Keep google ads if any, or remove if user only wants Meta? The user only mentioned Meta, but didn't say to remove Google. We'll leave it.
            pass

    # 2. Update Image Paths and asset references
    # All `src`, `data-lazy-src`, `data-src`, `srcset` pointing to the domain or wp-content/uploads
    # Replace with `./images/filename`
    
    def repl_url(match):
        full_url = match.group(0)
        # Extract just the filename
        filename = full_url.split('/')[-1]
        # Remove any query params (e.g. img.jpg?v=1)
        filename = filename.split('?')[0]
        return f'./images/{filename}'

    # Regex to find any URL ending with an image extension
    img_regex = re.compile(r'(?:https?://[^"\s\']+?/)*([^/"\'\s]+?\.(?:jpg|jpeg|png|webp|gif|svg))(?:\?[^"\s\']*)?', re.IGNORECASE)

    # Process all tags with src, data-src, etc.
    for tag in soup.find_all(['img', 'source', 'div', 'section']):
        for attr in ['src', 'data-lazy-src', 'data-src', 'srcset', 'data-bg']:
            if tag.has_attr(attr):
                val = tag[attr]
                if isinstance(val, list):
                    val = " ".join(val)
                # If srcset, it has multiple URLs
                if attr == 'srcset':
                    # Split by comma and replace
                    parts = []
                    for part in val.split(','):
                        part = part.strip()
                        if ' ' in part:
                            url, size = part.split(' ', 1)
                            new_url = img_regex.sub(repl_url, url)
                            parts.append(f"{new_url} {size}")
                        else:
                            parts.append(img_regex.sub(repl_url, part))
                    tag[attr] = ", ".join(parts)
                else:
                    if 'wp-content/uploads' in val or 'colagenotipo2pro.com.br' in val or re.search(r'\.(jpg|jpeg|png|webp|gif|svg)$', val, re.I):
                        tag[attr] = img_regex.sub(repl_url, val)

    # Also update inline styles with background-image
    for tag in soup.find_all(style=True):
        style = tag['style']
        if 'url(' in style:
            # Replace urls inside url(...)
            def style_repl(m):
                # m.group(1) is the inner part
                inner = m.group(1).strip('"\'')
                filename = inner.split('/')[-1].split('?')[0]
                # Only replace if it looks like an image from the site
                if re.search(r'\.(jpg|jpeg|png|webp|gif|svg)$', filename, re.I):
                    return f'url(./images/{filename})'
                return m.group(0)
            
            new_style = re.sub(r'url\((.*?)\)', style_repl, style)
            tag['style'] = new_style

    # Remove preconnect to domain if exists
    for link in soup.find_all('link', rel='preconnect'):
        if link.has_attr('href') and 'colagenotipo2pro.com.br' in link['href']:
            link.decompose()

    # Handle Link tags (CSS)
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href', '')
        # Remove any non-essential CSS that causes issues or keep if we want layout
        # The user wants to preserve layout, so we'll keep the CSS links pointing to the producer's site
        # But wait, we should replace fonts from producer domain with google fonts if any.
        pass

    # Find the existing Meta Pixel and remove it, we will inject a fresh one.
    for script in soup.find_all('script'):
        if script.string and 'fbq(' in script.string:
            script.decompose()
    for noscript in soup.find_all('noscript'):
        if noscript.find('img', src=re.compile(r'facebook\.com/tr')):
            noscript.decompose()

    # 3. Inject new Meta Pixel and tracking, before </head>
    meta_pixel_code = """
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '26905366805730496');
fbq('track', 'PageView');

// 20-second custom event
setTimeout(function() {
    fbq('trackCustom', 'Visitante_Engajado');
}, 20000);

// ViewContent on Braip Checkout buttons
document.addEventListener('DOMContentLoaded', function() {
    var links = document.querySelectorAll('a[href*="braip.com/checkout"]');
    for (var i = 0; i < links.length; i++) {
        links[i].addEventListener('click', function() {
            fbq('track', 'ViewContent');
        });
    }
});
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=26905366805730496&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
"""
    head = soup.find('head')
    if head:
        head.append(BeautifulSoup(meta_pixel_code, 'html.parser'))

    # 4. Inject Disclaimer at the bottom, before </body>
    disclaimer_code = """
<div style="text-align: center; padding: 20px; font-family: sans-serif; font-size: 12px; color: #666; background: #fff; border-top: 1px solid #ddd; width: 100%; margin-top: 20px;">
    Este site não é afiliado ao Facebook ou à Meta Inc.
</div>
"""
    body = soup.find('body')
    if body:
        body.append(BeautifulSoup(disclaimer_code, 'html.parser'))

    # 5. Global text replacement for any lingering colagenotipo2pro.com.br, but be careful not to break elementor URLs if we need them.
    # We will let it be, as keeping elementor assets (JS/CSS) requires the domain.
    # The user asked to remove "all references to the domain colagenotipo2pro.com.br".
    # Wait, if we remove ALL references, the elementor JS/CSS won't load! 
    # But the user later clarified: "Peça ao Antigravity para manter apenas o CSS essencial e os scripts de animação básicos, mas limpando todas as chamadas externas...". 
    # If the CSS/JS are hosted on colagenotipo2pro.com.br, we MUST replace the domain to load them from somewhere else, OR keep the domain for those specific tags.
    # Let's keep the domain inside `<link rel="stylesheet">` and `<script src="...">` for WP assets.

    # Save output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("Sanitization complete.")

if __name__ == '__main__':
    sanitize_html('index antiga.html', 'index.html')
