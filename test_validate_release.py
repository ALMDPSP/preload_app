import hashlib
import json
from release import APP_VERSION
from validate_release import validate_release


def test_shipped_application_is_complete():
    assert validate_release()==[]


def test_partial_upload_identifies_missing_and_old_assets(tmp_path):
    (tmp_path/'static').mkdir()
    (tmp_path/'static'/'ui.js').write_text('old version')
    expected=hashlib.sha256(b'new version').hexdigest()
    (tmp_path/'release_manifest.json').write_text(json.dumps({'version':APP_VERSION,
        'files':{'static/ui.js':expected,'templates/index.html':expected}}))
    errors=validate_release(tmp_path)
    assert 'static/ui.js diferente desta versão' in errors
    assert 'templates/index.html ausente' in errors


def test_missing_or_empty_manifest_is_rejected(tmp_path):
    assert validate_release(tmp_path)
    (tmp_path/'release_manifest.json').write_text(json.dumps({'version':APP_VERSION,'files':{}}))
    assert 'manifesto sem arquivos' in validate_release(tmp_path)
