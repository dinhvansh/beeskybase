"""Embed shared cloud UI assets into the standalone production template.

Run after editing semantic tokens, combo adapter or table controls. No runtime
filesystem dependency is introduced: frozen distributions still ship one HTML.
"""
from pathlib import Path
import base64
import re

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / 'cloud-preview'
TEMPLATE = ROOT / 'beesky/cloud/dashboard.html'

def read(name):
    return (PREVIEW / name).read_text(encoding='utf-8')

def embed_font(match):
    data = (PREVIEW / match.group(1)).read_bytes()
    return "url('data:font/woff2;base64," + base64.b64encode(data).decode('ascii') + "')"

def build():
    html = TEMPLATE.read_text(encoding='utf-8')
    tokens = re.sub(r"url\('(assets/fonts/[^']+)'\)", embed_font, read('design-tokens.css'))
    enterprise = read('enterprise.css')
    combo_style = enterprise[enterprise.index('.bee-select-trigger,.bee-select-search'):enterprise.index('.ops-agent,.ops-flow-card')]
    combo_icon = "const icon=n=>'<svg class=\"icon\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"'+(n==='check'?'M5 12l4 4L19 6':'M6 9l6 6 6-6')+'\"/></svg>';"
    blocks = {
        'SHARED_CSS': tokens + '\n' + read('components.css') + '\n' + combo_style,
        'COMBO': '(()=>{' + combo_icon + read('components.js') + '})();',
        'TABLE': read('table-controls.js'),
    }
    for name, content in blocks.items():
        start, end = f'/* BEESKY_{name}_START */', f'/* BEESKY_{name}_END */'
        a, b = html.index(start) + len(start), html.index(end)
        html = html[:a] + '\n' + content + '\n' + html[b:]
    TEMPLATE.write_text(html, encoding='utf-8')
    print('Embedded shared UI assets into cloud dashboard.')

if __name__ == '__main__':
    build()
