"""Restore only shipped interface files before validation and database initialization."""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile
from release import APP_VERSION


def restore_release_assets(root=None):
    root=(Path(root) if root is not None else Path(__file__).parent).resolve()
    manifest=json.loads((root/'release_manifest.json').read_text())
    if manifest.get('version')!=APP_VERSION:raise ValueError('Versão do pacote de interface incompatível.')
    archive=root/'release-assets.zip'
    expected=manifest.get('files',{}).get('release-assets.zip')
    if not expected or hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
        raise ValueError('release-assets.zip ausente, incompleto ou diferente desta versão.')
    expected_assets={name:digest for name,digest in manifest['files'].items()
                     if name.startswith(('static/','templates/'))}
    changed=0
    with ZipFile(archive) as bundle:
        entries={entry.filename:entry for entry in bundle.infolist() if not entry.is_dir()}
        if not expected_assets or set(entries)!=set(expected_assets):
            raise ValueError('A lista de arquivos da interface está incompleta.')
        # Inspect every destination before writing anything; no root files or databases are restored.
        prepared=[]
        for name,entry in entries.items():
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or path.parts[0] not in ('static','templates'):
                raise ValueError('Caminho inválido no pacote de interface.')
            destination=root/name
            if not destination.resolve().is_relative_to(root):
                raise ValueError('Destino de interface fora da aplicação.')
            content=bundle.read(entry)
            if hashlib.sha256(content).hexdigest()!=expected_assets[name]:
                raise ValueError('Arquivo de interface incompatível: '+name)
            prepared.append((destination,content))
        for destination,content in prepared:
            if destination.is_file() and destination.read_bytes()==content:continue
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(content)
            changed+=1
    return changed


if __name__=='__main__':
    try:
        changed=restore_release_assets()
        print('[inicialização] Interface '+APP_VERSION+' conferida; '+str(changed)+' arquivo(s) restaurado(s).',flush=True)
    except (OSError,ValueError,KeyError,BadZipFile) as error:
        print('[inicialização] Não foi possível preparar a interface: '+str(error),flush=True)
        raise SystemExit(1)
