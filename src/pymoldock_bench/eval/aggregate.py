from __future__ import annotations
import math
from collections import Counter

def macro_mean(values):
    values = list(values); return sum(values) / len(values) if values else 0.0
def geometric_mean(values):
    values = [max(0.0, float(x)) for x in values]
    return math.prod(values) ** (1 / len(values)) if values else 0.0

def summarize_results(rows):
    rows=list(rows); n=len(rows)
    def rate(pred): return sum(bool(pred(r)) for r in rows)/n if n else 0.0
    return {
        "episodes": n,
        "autonomous_completion_rate": rate(lambda r: r.get("autonomous_success", r.get("task_success", False))),
        "task_success_rate": rate(lambda r: r.get("task_success", False)),
        "needs_input_rate": rate(lambda r: r.get("human_assistance_required", False)),
        "timeout_rate": rate(lambda r: r.get("cua_outcome") == "timeout"),
        "artifact_success_rate": rate(lambda r: r.get("submission_present", False) and r.get("final_pse_present", False)),
        "pose_buckets": dict(Counter(r.get("pose_bucket") for r in rows if r.get("pose_bucket"))),
    }
