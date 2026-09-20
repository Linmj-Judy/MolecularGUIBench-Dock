import pytest
from pymoldockbench.exporter import export_selected_pose

def test_export_selected_pose_is_safe(tmp_path):
    workspace=tmp_path/"w"; workspace.mkdir(); source=workspace/"pose.sdf"; source.write_text("pose")
    out=tmp_path/"out"/"selected.sdf"; assert export_selected_pose(source,out,workspace)==out
    with pytest.raises(FileExistsError): export_selected_pose(source,out,workspace)
    with pytest.raises(ValueError): export_selected_pose(tmp_path/"outside.sdf",tmp_path/"x",workspace)
