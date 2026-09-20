import zipfile
from pymoldock_bench.data.prepare_posebusters import safe_extract, build_index

def test_safe_extract_and_index(tmp_path):
    z = tmp_path / "x.zip"
    with zipfile.ZipFile(z, "w") as f: f.writestr("case/receptor.pdb", "ATOM")
    out = tmp_path / "out"; safe_extract(z, out); idx = build_index(out, tmp_path / "index.json")
    assert "receptor.pdb" in idx.read_text()

