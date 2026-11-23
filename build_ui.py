"""Build a versioned UI loader while preserving individual script scope and order."""
import json
from pathlib import Path
from release import APP_VERSION

ROOT=Path(__file__).parent


def build_ui():
    parts=[]
    for item in json.loads((ROOT/'ui-sources.json').read_text()):
        name=item.get('src','initialization')
        parts.append({'name':name,'code':(ROOT/name).read_text() if 'src' in item else item['inline']})
    source='/* Complete Cutover Online interface '+APP_VERSION+'. */\n'
    source+='document.body.dataset.interfaceVersion='+json.dumps(APP_VERSION)+';\n'
    source+='(()=>{const parts='+json.dumps(parts,ensure_ascii=False)+';\n'
    source+='for(const part of parts){const script=document.createElement("script");script.dataset.source=part.name;script.textContent=part.code;document.body.append(script);script.remove();}})();\n'
    output=ROOT/'static'/('app-'+APP_VERSION+'.js')
    output.write_text(source)
    return output


if __name__=='__main__':print(build_ui())
