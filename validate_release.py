"""Check the shipped application before migrations or database access."""
import hashlib
import json
from pathlib import Path
from release import APP_VERSION


def validate_release(root=None):
    root=Path(root) if root is not None else Path(__file__).parent
    try:
        manifest=json.loads((root/'release_manifest.json').read_text())
    except (OSError,ValueError):
        return ['release_manifest.json ausente ou inválido']
    problems=[]
    if manifest.get('version')!=APP_VERSION:problems.append('versão do pacote diferente de release.py')
    for name,expected in manifest.get('files',{}).items():
        path=root/name
        try:actual=hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            problems.append(name+' ausente');continue
        if actual!=expected:problems.append(name+' diferente desta versão')
    if not manifest.get('files'):problems.append('manifesto sem arquivos')
    return problems


if __name__=='__main__':
    problems=validate_release()
    if problems:
        print('[inicialização] Atualização incompleta. Envie a base completa preservando static e templates.',flush=True)
        for item in problems:print('[inicialização] '+item,flush=True)
        raise SystemExit(1)
    print('[inicialização] Base completa conferida - versão '+APP_VERSION,flush=True)
