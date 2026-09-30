from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "research" / "external_inputs"


def build(contract_path: Path, output_dir: Path, threshold: float, policy: str) -> None:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    checkpoint = list(contract["checkpoint_validation"])
    calibration = list(contract["calibration"])
    confirmation = [name for name in calibration if name not in checkpoint]
    weight_name = "edge_predictor_best.pth"
    weight_receipt = contract["artifacts"][weight_name]
    payload = {
        "status": "selection_frozen_before_confirmation_and_audit",
        "holdout_embryo": contract["holdout_embryo"],
        "weights_sha256": weight_receipt["sha256"],
        "parent_contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "checkpoint_validation_movies": checkpoint,
        "tuning_movies": checkpoint,
        "confirmation_movies": confirmation,
        "audit_movies": list(contract["audit"]),
        "threshold_grid": [0.95, 0.97, 0.985, 0.99, 0.995],
        "edge_candidate_threshold": 0.5,
        "candidate_pool_degree_limits": None,
        "inference_gpu_count": 1,
        "inference_data_parallel": False,
        "inference_unet_batch_size": 4,
        "ilp_public_appearance_disappearance": [0.0, 1.5],
        "ilp_support_appearance_disappearance": [0.1, 0.1],
        "selected_threshold": threshold,
        "selected_policy": policy,
        "postselection_physical_arms": {
            "selected_base": None,
            "physical_prune_4_2": [4.0, 2.0],
            "physical_prune_7_4": [7.0, 4.0],
        },
        "postselection_arm_status": "frozen_before_confirmation_and_untouched_audit",
        "postselection_scope": "mechanism-only; independent EXP005/008 donor consensus is not reproduced",
        "tuning_results": [],
        "reconstruction_receipt": "threshold/policy recovered from immutable upstream audit run-log; split and weight identity recovered from parent contract",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"loeo_{contract['holdout_embryo']}_selection.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


def main() -> None:
    build(BASE / "exp009" / "loeo_44b6_contract.json", BASE / "exp011", 0.985, "registered_hungarian")
    build(BASE / "exp010" / "loeo_6bba_contract.json", BASE / "exp012", 0.99, "registered_hungarian")


if __name__ == "__main__":
    main()
