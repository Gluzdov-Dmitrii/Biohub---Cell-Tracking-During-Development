"""Separate guarded, read-only EXP239 recheck; preserve the original receipt."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import verify_exp239_division_fn_taxonomy as verifier


if not __debug__:
    raise RuntimeError("EXP239 guarded recheck requires Python assertions")

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OLD = REPORTS / "exp239_division_fn_taxonomy_verified_20260927.json"
CORRECTION = REPORTS / "exp239_verifier_postrun_guard_correction_20260927.json"
OUT = REPORTS / "exp239_guarded_readonly_recheck_20260927.json"
EXPECTED_OLD_SHA = "ccd78a08822a1bf603cf4e1d9241df9f3ee8eef27f26559a263188195148cc57"
EXPECTED_CORRECTION_SHA = "69ed99e85c7dcaf4caff96d7cd399516deececcce5a6c3d57156252586c46088"
EXPECTED_VERIFIER_SHA = "e07e33a854d91c9db90a8f39b8e5c49fbbd9b4887d62fe25439e329e7f77a600"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not OUT.exists(), "guarded recheck already recorded"
    assert sha(OLD) == EXPECTED_OLD_SHA
    assert sha(CORRECTION) == EXPECTED_CORRECTION_SHA
    assert sha(Path(verifier.__file__)) == EXPECTED_VERIFIER_SHA
    old = json.loads(OLD.read_text(encoding="utf-8"))
    correction = json.loads(CORRECTION.read_text(encoding="utf-8"))
    assert old["status"] == "PASS_EXP239_INDEPENDENT_COMPLETION_VERIFICATION"
    assert correction["completed_verification"]["receipt_sha256"] == EXPECTED_OLD_SHA
    assert correction["subsequent_source_correction"]["sha256"] == EXPECTED_VERIFIER_SHA
    checked = verifier.remote_check()
    assert checked == old["remote"], "guarded readback disagrees with original receipt"
    receipt = {
        "status": "PASS_EXP239_GUARDED_READONLY_RECHECK",
        "original_receipt_sha256": EXPECTED_OLD_SHA,
        "postrun_correction_sha256": EXPECTED_CORRECTION_SHA,
        "executed_guarded_verifier_sha256": EXPECTED_VERIFIER_SHA,
        "recheck_script_sha256": sha(Path(__file__)),
        "python_assertions_enabled": __debug__,
        "remote_pythonoptimize": "0",
        "remote_readback_identical_to_original": True,
        "remote": checked,
        "source_labels_opened_by_recheck": False,
        "reciprocal_target_labels_read": False,
        "remote_mutation": False,
        "kaggle_post": False,
        "original_receipt_edited": False,
    }
    with OUT.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"status": receipt["status"], "receipt": str(OUT),
                      "receipt_sha256": sha(OUT), "source_division_fns": checked["source_division_fns"]}))


if __name__ == "__main__":
    main()
