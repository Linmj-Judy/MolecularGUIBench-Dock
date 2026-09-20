from pymoldock_bench.data.report import write_dataset_report

def test_dataset_report_writes_json_and_csv(tmp_path):
    root=tmp_path/"episodes"; (root/"E1").mkdir(parents=True)
    (root/"E1"/"episode.json").write_text('{"target_id":"T1","pose_bucket":"P0"}')
    out=write_dataset_report(root,tmp_path/"report.json")
    assert out.exists() and (tmp_path/"report.csv").exists()
