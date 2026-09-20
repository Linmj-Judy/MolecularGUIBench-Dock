from pymoldock_bench.data.isolation import assert_public_path
import pytest

def test_private_path_rejected(tmp_path):
    with pytest.raises(ValueError): assert_public_path(tmp_path/"private"/"truth.json", tmp_path)
