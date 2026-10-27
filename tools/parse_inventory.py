"""Markdown-инвентаризация машин → список узлов и связей.

Формат файла inventory/<машина>.md (его удобно поручать агенту, который обходит машину только чтением):

    ### node-id
    - name: Человеческое название
    - host: vps | laptop | homelab | cloud
    - kind: service | timer | db | ...
    - group: core | network | ...
    - status: up | partial | failed | down | disabled | staging | mothballed | unknown
    - statusNote: пояснение к статусу (необязательно)
    - purpose: зачем это нужно
    - how: как устроено
    - tech: стек
    - links:
      - -> other-id : канал : что передаётся
      - <- other-id : канал : что приходит
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELD_RE = re.compile(r'^- ([a-zA-Z_]+):\s*(.*)$')
HEAD_RE = re.compile(r'^### +`?([A-Za-z0-9][\w.\-]*)`?\s*$')
FIELDS = ('name', 'host', 'kind', 'group', 'status', 'statusnote', 'purpose', 'how', 'tech', 'links')


def parse_links(text, src):
    out = []
    text = text.replace('`', '')
    parts = re.split(r'[;\n]', text)
    for p in parts:
        p = re.sub(r'^-\s+', '', p.strip()).strip()
        m = re.match(r'^(->|<-|→|←)\s*([A-Za-z0-9][\w.\-]*)\s*(.*)$', p)
        if not m:
            continue
        arrow, tgt, rest = m.groups()
        rest = rest.strip()
        rest = re.sub(r'^:\s*', '', rest)
        bits = re.split(r'\s+:\s*|\s*:\s+', rest, maxsplit=1) if rest else []
        via = bits[0].strip() if bits else ''
        what = bits[1].strip() if len(bits) > 1 else ''
        if arrow in ('->', '→'):
            out.append({'source': src, 'target': tgt, 'via': via, 'what': what})
        else:
            out.append({'source': tgt, 'target': src, 'via': via, 'what': what})
    return out


def parse_file(path: Path, origin: str) -> list[dict]:
    nodes, cur, field = [], None, None
    for line in path.read_text(encoding='utf-8').splitlines():
        h = HEAD_RE.match(line)
        if h:
            cur = {'id': h.group(1), 'f': {}}
            nodes.append(cur)
            field = None
            continue
        if line.startswith('#'):
            cur, field = None, None
            continue
        if cur is None:
            continue
        fm = FIELD_RE.match(line)
        if fm and fm.group(1).lower() in FIELDS:
            field = fm.group(1).lower()
            cur['f'][field] = fm.group(2).strip()
            continue
        if field and line.strip():
            cur['f'][field] += '\n' + line.strip()
    out = []
    for n in nodes:
        f = n['f']
        rec = {k: f.get(k, '').strip() for k in FIELDS if k != 'links'}
        rec['statusNote'] = rec.pop('statusnote')
        rec.update(id=n['id'], origin=origin, links=parse_links(f.get('links', ''), n['id']))
        out.append(rec)
    return out


def parse_all(folder: Path) -> list[dict]:
    nodes = []
    for path in sorted(folder.glob('*.md')):
        if path.stem != 'problems':
            nodes += parse_file(path, path.stem)
    return nodes


if __name__ == '__main__':
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'inventory'
    nodes = parse_all(folder)
    json.dump(nodes, sys.stdout, ensure_ascii=False, indent=1)
