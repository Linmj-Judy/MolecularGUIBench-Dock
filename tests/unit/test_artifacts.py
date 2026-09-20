import pytest
from pymoldock_bench.runner.artifact_collector import collect_expected

def test_collect_expected_is_non_destructive(tmp_path):
    root=tmp_path/"workspace"; root.mkdir(); (root/"submission.json").write_text('{}')
    out=tmp_path/"out"; assert collect_expected(root,["submission.json"],out)==[out/"submission.json"]
    with pytest.raises(FileExistsError): collect_expected(root,["submission.json"],out)
