"""Store leadership resolved from the supplied store list without rewriting saved records."""
import json
import re
from functools import lru_cache
from pathlib import Path


def store_key(code):
    value=str(code).strip().upper()
    match=re.fullmatch(r'(VD|L)?0*(\d+)',value)
    return (match.group(1) or '')+str(int(match.group(2))) if match else value


@lru_cache(maxsize=1)
def reference():
    rows=json.loads(Path(__file__).with_name('store_organization.json').read_text(encoding='utf-8'))
    return {store_key(row['code']):row for row in rows}


def organization_for(code,previous=None):
    previous=previous or {}
    key=store_key(code)
    row=reference().get(key)
    if row is None and key.isdigit():
        matches=[value for candidate,value in reference().items() if store_key(candidate.lstrip('VDL'))==key]
        row=matches[0] if len(matches)==1 else None
    source=row or {}
    return {
        'gr':source.get('gr') or previous.get('gr') or '',
        'regional':source.get('regional') or previous.get('regional') or '',
        'ggr':source.get('ggr',''),
        'ggr_region':source.get('ggr_region',''),
        'division':source.get('division',''),
        'division_region':source.get('division_region',''),
        'organization_matched':row is not None,
    }
