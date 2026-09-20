import json
import pytest
from pymoldock_bench.cua.ark_client import ArkCUAAuthRequired, ArkCUAClient

def test_auth_required_is_normalized(monkeypatch, tmp_path):
    skill=tmp_path/"skill"; (skill/"scripts").mkdir(parents=True); (skill/"scripts"/"cua.py").write_text("")
    class Result:
        stdout=json.dumps({"ok":False,"error":{"code":"AUTH_REQUIRED","message":"credential redacted"}})
        returncode=1
    monkeypatch.setattr("subprocess.run", lambda *a, **k: Result())
    with pytest.raises(ArkCUAAuthRequired) as exc:
        ArkCUAClient(skill).auth_status()
    assert "AUTH_REQUIRED" in str(exc.value)
    assert "credential" not in str(exc.value)
