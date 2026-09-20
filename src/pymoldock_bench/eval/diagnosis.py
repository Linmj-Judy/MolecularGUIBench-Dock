from ..schemas import Episode, GroundTruth, Submission, EvaluationResult
from .interface import interface_scores

def evaluate(episode: Episode, submission: Submission, truth: GroundTruth) -> EvaluationResult:
    truth_interface = truth.interface_residues or truth.native_interface
    scores = interface_scores(submission.interface_residues, truth_interface)
    valid = {"yes": "valid", "no": "invalid"}.get(submission.physical_plausibility, submission.physical_plausibility)
    native_label = {"yes": "likely_correct", "no": "likely_incorrect"}.get(submission.native_likeness, submission.native_likeness)
    pb = None if truth.pb_valid is None else valid == ("valid" if truth.pb_valid else "invalid")
    native = None if truth.native_like is None else native_label == ("likely_correct" if truth.native_like else "likely_incorrect")
    return EvaluationResult(episode_id=episode.episode_id, interface_precision=scores["precision"],
        interface_recall=scores["recall"], interface_f1=scores["f1"], pb_valid_correct=pb,
        native_like_correct=native, task_success=submission.status == "completed",
        metrics={"interface_f1": scores["f1"]})
