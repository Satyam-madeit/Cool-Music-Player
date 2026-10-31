import os
import re
import requests
from pathlib import Path

font_dir = Path('frontend/fonts')
font_dir.mkdir(parents=True, exist_ok=True)

# Google Fonts CSS URLs
fonts = {
    'Hanken Grotesk': 'https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@100..900&display=swap',
    'Space Grotesk': 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap',
    'Space Mono': 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap',
    'Material Symbols Outlined': 'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap',
}

def download_font_family(name, css_url):
    print(f'Downloading {name}...')
    css = requests.get(css_url).text
    # Find font-face src urls
    urls = re.findall(r'url\((https?://[^)]+)\)', css)
    for url in urls:
        # Accept ttf, woff2, woff
        if any(ext in url for ext in ('.ttf', '.woff2', '.woff')):
            fname = os.path.basename(url.split('?')[0])
            out_path = font_dir / fname
            if not out_path.exists():
                print(f'  {url}')
                data = requests.get(url).content
                out_path.write_bytes(data)
            else:
                print(f'  already have {fname}')
    # Save CSS with local paths
    def repl(m):
        url = m.group(1)
        if any(ext in url for ext in ('.ttf', '.woff2', '.woff')):
            fname = os.path.basename(url.split('?')[0])
            return f'url({fname})'
        return m.group(0)
    local_css = re.sub(r'url\((https?://[^)]+)\)', repl, css)
    css_file = font_dir / f'{name.lower().replace(" ", "-")}.css'
    css_file.write_text(local_css)
    print(f'  saved {css_file}')

for name, url in fonts.items():
    download_font_family(name, url)

print('Done.')