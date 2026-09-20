from __future__ import annotations

import json
from typing import Any

from ..schemas import Submission


def parse_submission(payload: str | bytes | dict[str, Any]) -> Submission:
    """Parse only the structured submission object; free-form text is rejected."""
    if isinstance(payload, (str, bytes)):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise TypeError("submission must be a JSON object")
    return Submission.model_validate(payload)
