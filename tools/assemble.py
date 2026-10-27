"""Узлы инвентаризации + meta.json + problems.md → data/infra.json для viewer.html.

Проверяет то, что ломало карту на живых данных: ссылки на несуществующие узлы, неизвестные машины,
контуры и статусы, дубли id и связей. Ошибки печатаются списком, а не роняют сборку на первой.
"""
import json
import sys
from pathlib import Path

from parse_inventory import parse_all

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {'up', 'partial', 'staging', 'failed', 'down', 'disabled', 'mothballed', 'unknown'}


def assemble(folder: Path) -> tuple[dict, list[str]]:
    meta = json.loads((folder / 'meta.json').read_text(encoding='utf-8'))
    raw = parse_all(folder)
    warnings: list[str] = []
    nodes, seen = [], set()
    for n in raw:
        if n['id'] in seen:
            warnings.append(f"дубль id {n['id']} ({n['origin']}) — оставлен первый")
            continue
        seen.add(n['id'])
        if n['host'] not in meta['hosts']:
            warnings.append(f"{n['id']}: неизвестная машина {n['host']!r} → cloud")
            n['host'] = 'cloud'
        if n['group'] not in meta['groups']:
            warnings.append(f"{n['id']}: неизвестный контур {n['group']!r}")
        status = n['status'].split()[0].lower() if n['status'] else 'unknown'
        if status not in STATUSES:
            warnings.append(f"{n['id']}: статус {n['status']!r} → unknown")
            status = 'unknown'
        nodes.append({k: n[k] for k in ('id', 'host', 'kind', 'group', 'purpose', 'how', 'tech')}
                     | {'name': n['name'] or n['id'], 'status': status, 'statusNote': n['statusNote']})
    links, pairs = [], set()
    for n in raw:
        for link in n['links']:
            key = (link['source'], link['target'], link['via'])
            if link['source'] not in seen or link['target'] not in seen:
                warnings.append(f"связь {link['source']} → {link['target']}: узла нет, пропущена")
                continue
            if key not in pairs:
                pairs.add(key)
                links.append(link)
    problems_md = folder / 'problems.md'
    problems = [line[2:].strip() for line in problems_md.read_text(encoding='utf-8').splitlines()
                if line.startswith('- ')] if problems_md.exists() else []
    data = {'snapshot': meta.get('snapshot', ''), 'hostOrder': meta.get('hostOrder'), 'hosts': meta['hosts'],
            'groups': meta['groups'], 'nodes': nodes, 'links': links, 'problems': problems}
    return data, warnings


if __name__ == '__main__':
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'inventory'
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'data' / 'infra.json'
    data, warnings = assemble(folder)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    for w in warnings:
        print('!', w, file=sys.stderr)
    print(f"{out.name}: {len(data['nodes'])} узлов, {len(data['links'])} связей, предупреждений {len(warnings)}")
