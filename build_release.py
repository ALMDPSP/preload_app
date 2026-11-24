"""Build the versioned interface, recovery archive and integrity manifest."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from build_ui import build_ui
from release import APP_VERSION


def build_release():
    root=Path(__file__).parent
    build_ui()
    assets=sorted(p for folder in ('static','templates') for p in (root/folder).rglob('*') if p.is_file())
    with ZipFile(root/'release-assets.zip','w',ZIP_DEFLATED) as archive:
        for path in assets:archive.write(path,path.relative_to(root).as_posix())
    sources=[p for p in root.iterdir() if p.is_file() and not p.name.startswith('test_') and
             (p.suffix in ('.py','.sh','.json','.txt') or p.name=='release-assets.zip') and p.name!='release_manifest.json']
    files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(assets+sources)}
    (root/'release_manifest.json').write_text(json.dumps({'version':APP_VERSION,'files':files},ensure_ascii=False,indent=2)+'\n')
    return len(files)


if __name__=='__main__':print('Base '+APP_VERSION+' preparada: '+str(build_release())+' arquivos conferidos.')
