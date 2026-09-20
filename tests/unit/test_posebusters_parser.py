from pymoldock_bench.eval.posebusters import parse_posebusters_output

def test_posebusters_csv_parser():
    r=parse_posebusters_output("rmsd,no_clashes_with_protein,mol_ok\n1.2,True,True\n")
    assert r.pb_valid is True and r.rmsd_le_2a is True
    assert r.individual_checks["no_clashes_with_protein"] is True
