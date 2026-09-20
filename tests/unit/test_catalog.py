from pymoldock_bench.data.results_catalog import summarize_catalog

def test_catalog(tmp_path):
    p=tmp_path/"r.csv"; p.write_text("target,valid\na,true\n")
    assert summarize_catalog(p) == {"rows":1,"columns":2}
