def pose_bucket(rmsd, pb_valid, centroid_distance=None, native_interface_f1=None, meaningful_contacts=0, clash=False):
    if rmsd is None or pb_valid is None: return "unknown"
    if rmsd <= 2.0: return "P0" if pb_valid else "P1"
    if centroid_distance is not None and centroid_distance <= 2.5 and (native_interface_f1 or 0) >= .5: return "P2"
    if clash or centroid_distance is None or centroid_distance > 6.0 or meaningful_contacts < 3: return "P4"
    if centroid_distance <= 6.0: return "P3"
    return "P4"
