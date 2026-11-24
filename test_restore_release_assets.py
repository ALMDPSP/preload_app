import hashlib
import json
from zipfile import ZipFile
import pytest
from release import APP_VERSION
from restore_release_assets import restore_release_assets


def prepare(root,files):
    archive=root/'release-assets.zip'
    with ZipFile(archive,'w') as target:
        for name,content in files.items():target.writestr(name,content)
    manifest={'version':APP_VERSION,'files':{name:hashlib.sha256(value).hexdigest() for name,value in files.items()}}
    manifest['files']['release-assets.zip']=hashlib.sha256(archive.read_bytes()).hexdigest()
    (root/'release_manifest.json').write_text(json.dumps(manifest))


def test_restores_missing_or_stale_templates_without_touching_database(tmp_path):
    files={'templates/index.html':b'new dashboard','templates/login.html':b'new login','templates/mfa.html':b'new MFA','static/app.js':b'new interface'}
    prepare(tmp_path,files)
    (tmp_path/'templates').mkdir();(tmp_path/'templates/index.html').write_text('old dashboard')
    database=tmp_path/'dev.sqlite';database.write_bytes(b'existing data must remain unchanged')
    assert restore_release_assets(tmp_path)==4
    assert all((tmp_path/name).read_bytes()==content for name,content in files.items())
    assert database.read_bytes()==b'existing data must remain unchanged'
    assert restore_release_assets(tmp_path)==0


def test_restore_rejects_invalid_bundle_before_writing(tmp_path):
    prepare(tmp_path,{'templates/index.html':b'new dashboard'})
    (tmp_path/'release-assets.zip').write_bytes(b'incomplete upload')
    with pytest.raises(ValueError,match='release-assets.zip'):restore_release_assets(tmp_path)
    assert not (tmp_path/'templates').exists()


def test_restore_rejects_paths_outside_interface(tmp_path):
    prepare(tmp_path,{'templates/../../dev.sqlite':b'must not be written'})
    with pytest.raises(ValueError,match='Caminho'):restore_release_assets(tmp_path)
    assert not (tmp_path/'dev.sqlite').exists()
