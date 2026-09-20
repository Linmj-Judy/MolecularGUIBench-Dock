def __init_plugin__(app=None):
    """PyMOL plugin entry point. Registration is optional in headless tests."""
    if app is not None and hasattr(app, "menuBar"):
        return None
    return None

def validate_and_write_submission(episode_id: str, output, *, physical_plausibility: str,
                                  native_likeness: str, confidence: float, failure_modes=None,
                                  interactions=None, selected_pose=None):
    """Headless equivalent of the panel's Submit button."""
    from pymoldock_bench.schemas import Submission
    from pathlib import Path
    if physical_plausibility not in {"valid", "invalid", "uncertain"}: raise ValueError("invalid physical plausibility")
    if native_likeness not in {"likely_correct", "likely_incorrect", "uncertain"}: raise ValueError("invalid native likeness")
    result=Submission(episode_id=episode_id, status="completed", physical_plausibility=physical_plausibility,
                      native_likeness=native_likeness, confidence=confidence, failure_category=(failure_modes or [None])[0], selected_pose=selected_pose)
    path=Path(output); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result
