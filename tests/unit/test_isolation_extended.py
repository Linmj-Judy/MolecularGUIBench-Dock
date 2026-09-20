import pytest
from pymoldock_bench.data.isolation import assert_private_data_not_exposed

def test_private_symlink_rejected(tmp_path):
    public, private = tmp_path / "public", tmp_path / "private"
    public.mkdir(); private.mkdir(); (private / "native.sdf").write_text("gt")
    (public / "native_link").symlink_to(private / "native.sdf")
    with pytest.raises(ValueError): assert_private_data_not_exposed(public, private)
