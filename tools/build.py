"""viewer.html + data/infra.json → один самодостаточный HTML (работает офлайн, открывается двойным кликом).

Библиотеки (three.js, 3d-force-graph, force-graph) скачиваются один раз в tools/vendor/ и встраиваются в файл.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = Path(__file__).resolve().parent / 'vendor'
SCRIPTS = {
    'https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js': 'three.min.js',
    'https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js': 'OrbitControls.js',
    'https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/renderers/CSS2DRenderer.js': 'CSS2DRenderer.js',
    'https://cdn.jsdelivr.net/npm/3d-force-graph@1.73.4/dist/3d-force-graph.min.js': '3d-force-graph.min.js',
    'https://cdn.jsdelivr.net/npm/force-graph@1.47.4/dist/force-graph.min.js': 'force-graph.min.js',
}


def safe_js(code: str) -> str:
    return re.sub(r'</(script)', r'<\\/\1', code, flags=re.I).replace('<!--', '<\\!--')


def dedupe_text(t: str) -> str:
    """Агенты-инвентаризаторы любят повторять одну мысль дважды — убираем предложения, почти целиком
    повторяющие уже сказанное."""
    if not t:
        return t
    kept, seen = [], []
    for sen in re.split(r'(?<=[.!?])\s+', t.strip()):
        w = {x for x in re.findall(r'\w+', sen.lower()) if len(x) > 2}
        union = set().union(*seen) if seen else set()
        if w and len(w & union) / len(w) >= 0.8:
            continue
        kept.append(sen)
        seen.append(w)
    return ' '.join(kept)


def vendor(url: str, name: str) -> str:
    path = VENDOR / name
    if not path.exists():
        VENDOR.mkdir(exist_ok=True)
        with urllib.request.urlopen(url, timeout=60) as r:
            path.write_bytes(r.read())
    return path.read_text(encoding='utf-8')


def build(data_path: Path, out: Path) -> None:
    html = (ROOT / 'viewer.html').read_text(encoding='utf-8')
    data = json.loads(data_path.read_text(encoding='utf-8'))
    for n in data['nodes']:
        for f in ('purpose', 'how', 'statusNote'):
            n[f] = dedupe_text(n.get(f) or '')
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    payload = payload.replace('</', '<\\/').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    assert html.count('/*DATA*/null') == 1
    html = html.replace('/*DATA*/null', payload)
    for url, name in SCRIPTS.items():
        tag = f'<script src="{url}"></script>'
        assert html.count(tag) == 1, url
        html = html.replace(tag, '<script>' + safe_js(vendor(url, name)) + '</script>', 1)
    assert 'cdn.jsdelivr' not in html
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(out.name, out.stat().st_size)


if __name__ == '__main__':
    data_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'infra.json'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'dist' / 'infra-map.html'
    build(data_path, out)
