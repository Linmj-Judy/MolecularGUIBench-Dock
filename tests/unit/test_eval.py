import numpy as np
from pymoldock_bench.eval import interface_scores, kabsch_rmsd
from pymoldock_bench.eval.rmsd import symmetry_aware_rmsd
from pymoldock_bench.eval.pose_buckets import pose_bucket

def test_interface_f1():
    assert interface_scores(["A:1", "A:2"], ["A:2", "A:3"])["f1"] == .5

def test_kabsch_translation_rotation_invariant():
    p = np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
    q = p + [3., -2., 4.]
    assert kabsch_rmsd(p, q) < 1e-8

def test_symmetry_mapping_and_pose_buckets():
    p=np.array([[1.,0,0],[-1.,0,0],[0,1.,0],[0,-1.,0]])
    q=p[[1,0,3,2]]
    assert symmetry_aware_rmsd(p,q,[[0,1],[2,3]]) < 1e-8
    assert pose_bucket(1.5, True) == "P0"
    assert pose_bucket(1.5, False) == "P1"
    assert pose_bucket(3.0, True, 2.0, .6, 5) == "P2"
