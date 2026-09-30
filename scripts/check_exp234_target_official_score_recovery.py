"""Reconcile the completed EXP234 scorer after the verifier token-order failure.

Default mode is read-only. Explicit --write-receipt creates the local score
receipt once after the stopped state and exact remote output hashes are pinned.
Neither mode restarts the scorer or changes the original STOPPED handoff.
"""
import argparse
import json

import verify_exp234_target_official_scorer as verifier


ROOT = verifier.ROOT
HANDOFF = ROOT / "reports/exp234_target_score_handoff_20260927.json"
SCORER = ROOT / "scripts/score_exp234_target_official.py"
EXPECTED = {
    "handoff_sha256": "336757ebebf325712f22ffc80d432d35a274654a81d5fc60666b8f0cb7ae9bc1",
    "prepare_sha256": "1b4d5cc33f9e1130dd1488ca213df3ad26b6a361e778551e27e04442fce2aec6",
    "launch_sha256": "219f874cc788f861a6a3c71330a4a2b70b55fb745cc2c40dffb6184d59b96b88",
    "scorer_source_sha256": "64cc0fe20c0a7b14eb18d2170470ada1cd1e04a0e196ad3d82e67f7957409877",
    "gate_sha256": "37b07134c9ff27bf3eaf318d51185fdefb11737cb4721a1bf2fdd390dd94a664",
    "result_sha256": "124541f647432c7b01a9e2223ef76524927ff2587ec95f8609f7b1765e43c07c",
}


def main(*, write_receipt=False):
    assert verifier.sha(HANDOFF) == EXPECTED["handoff_sha256"]
    handoff = json.loads(HANDOFF.read_text())
    assert handoff["status"] == "STOPPED_EXP234_TARGET175_SCORE_HANDOFF"
    assert handoff["verify_score_returncode"] == 1
    assert handoff["score_exit"]["returncode"] == 0
    assert handoff["score_exit"]["timeout"] is False
    assert verifier.sha(verifier.PREPARE) == EXPECTED["prepare_sha256"]
    assert verifier.sha(verifier.LAUNCH) == EXPECTED["launch_sha256"]
    assert verifier.sha(SCORER) == EXPECTED["scorer_source_sha256"]
    assert not verifier.RECEIPT.exists()

    checked = verifier.verify(write_receipt=False)
    assert checked["status"] == "VERIFIED_EXP234_TARGET175_OFFICIAL"
    assert checked["metric_identity"] == "HISTORICAL_EXP214_SUPPORT_PACK_REPLAY"
    assert checked["current_organizer_score"] is None
    assert checked["historical_exp214_score"] == checked["official_score"]
    assert checked["baseline_replay"] == "PASS_1e-12" and checked["rows"] == 175
    assert checked["gate_sha256"] == EXPECTED["gate_sha256"]
    assert checked["result_sha256"] == EXPECTED["result_sha256"]
    assert abs(checked["official_score"] - 0.7426705533442897) < 1e-15
    for path, key in ((HANDOFF, "handoff_sha256"),
                      (verifier.PREPARE, "prepare_sha256"),
                      (verifier.LAUNCH, "launch_sha256"),
                      (SCORER, "scorer_source_sha256")):
        assert verifier.sha(path) == EXPECTED[key]
    assert not verifier.RECEIPT.exists()
    if write_receipt:
        receipt = {**checked, "stopped_handoff_sha256": EXPECTED["handoff_sha256"],
                   "recovery_reason": "verifier_prediction_hash_token_order"}
        with verifier.RECEIPT.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({**checked,
                      "status": ("WROTE_EXP234_TARGET175_EXP214_PINNED_SCORE_RECEIPT" if write_receipt
                                 else "CHECK_ONLY_EXP234_TARGET175_EXP214_PINNED_RECONCILED"),
                      "original_handoff_sha256": EXPECTED["handoff_sha256"],
                      "score_receipt_written": write_receipt}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", action="store_true")
    main(write_receipt=parser.parse_args().write_receipt)
