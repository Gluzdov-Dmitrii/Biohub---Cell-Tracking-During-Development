"""Build the human-readable, search-friendly private-first experiment notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "outputs/research/exp130_official24_private_first"
OUTPUT = ROOT / "notebooks/biohub_private_first_oof_model_development.ipynb"


def markdown(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


def main() -> None:
    scratch = json.loads((RESULTS / "scratch_registered_result.json").read_text(encoding="utf-8"))
    zebra = json.loads((RESULTS / "zebrahub_registered_result.json").read_text(encoding="utf-8"))
    consensus = json.loads((RESULTS / "coordinate_consensus_result.json").read_text(encoding="utf-8"))
    dual_seed = json.loads(
        (RESULTS / "dual_seed_coordinate_consensus_result.json").read_text(encoding="utf-8")
    )
    repeat_scratch = json.loads(
        (RESULTS / "seed271828_scratch_registered_result.json").read_text(encoding="utf-8")
    )
    repeat_zebra = json.loads(
        (RESULTS / "seed271828_zebrahub_registered_result.json").read_text(encoding="utf-8")
    )
    low_lr = json.loads((RESULTS / "exp135_low_lr_registered_result.json").read_text(encoding="utf-8"))
    full_model = json.loads(
        (RESULTS / "exp136_full_model_registered_result.json").read_text(encoding="utf-8")
    )
    discriminative_lr = json.loads(
        (ROOT / "reports/exp138_discriminative_lr_20260909.json").read_text(encoding="utf-8")
    )
    source_threshold = json.loads(
        (ROOT / "reports/exp139_source_threshold_20260909.json").read_text(encoding="utf-8")
    )
    source_threshold_repeat = json.loads(
        (ROOT / "reports/exp140_source_threshold_seed314159_20260909.json").read_text(
            encoding="utf-8"
        )
    )
    weight_soup = json.loads(
        (ROOT / "reports/exp141_unet_weight_soup_20260909.json").read_text(encoding="utf-8")
    )
    detector_fusion = json.loads(
        (ROOT / "reports/exp142_dual_detector_fusion_20260909.json").read_text(
            encoding="utf-8"
        )
    )
    reciprocal_pilot = json.loads(
        (ROOT / "reports/exp143_reciprocal_7movie_pilot_20260909.json").read_text(
            encoding="utf-8"
        )
    )
    data_receipt = json.loads(
        (ROOT / "reports/exp137_data_stage_batch3_20260909.json").read_text(encoding="utf-8")
    )
    reciprocal_path = ROOT / "reports/exp137_full_reciprocal_20260909.json"
    reciprocal = (
        json.loads(reciprocal_path.read_text(encoding="utf-8"))
        if reciprocal_path.exists()
        else None
    )
    locked_path = ROOT / "reports/exp144_locked_reciprocal_audit_20260910.json"
    locked = json.loads(locked_path.read_text(encoding="utf-8")) if locked_path.exists() else None
    feature_tta_path = ROOT / "reports/exp145_feature_tta_development_20260910.json"
    feature_tta = (
        json.loads(feature_tta_path.read_text(encoding="utf-8"))
        if feature_tta_path.exists()
        else None
    )
    seed_consensus_path = ROOT / "reports/exp146_scratch_seed_consensus_result_20260910.json"
    seed_consensus = (
        json.loads(seed_consensus_path.read_text(encoding="utf-8"))
        if seed_consensus_path.exists()
        else None
    )
    safe_division_path = ROOT / "reports/exp147_safe_division_result_20260910.json"
    safe_division = (
        json.loads(safe_division_path.read_text(encoding="utf-8"))
        if safe_division_path.exists()
        else None
    )
    weak_feature_tta = json.loads(
        (ROOT / "reports/exp148_weak_linker_feature_tta_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    native_raw = json.loads(
        (ROOT / "reports/exp149_cached_native_ilp_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    native_geometry = json.loads(
        (ROOT / "reports/exp150_native_ilp_geometry_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    native_guided = json.loads(
        (ROOT / "reports/exp151_native_guided_division_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    dense_native = json.loads(
        (ROOT / "reports/exp152_dense_native_source_selection_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    division_signal = json.loads(
        (ROOT / "reports/exp153_division_supervision_diagnostic_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    external_edge = json.loads(
        (ROOT / "reports/exp154_external_edge_fixed_coordinates_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    external_weak = json.loads(
        (ROOT / "reports/exp155_external_weak_linker_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    external_confidence = json.loads(
        (ROOT / "reports/exp156_external_confidence_gate_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    division_recalibration = json.loads(
        (ROOT / "reports/exp157_division_positive_recalibration_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    visual_pair = json.loads(
        (ROOT / "reports/exp159_visual_daughter_pair_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    pretrained_pair = json.loads(
        (ROOT / "reports/exp160_pretrained_feature_pair_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    pair_ensemble = json.loads(
        (ROOT / "reports/exp164_visual_pair_rank_ensemble_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    pair_diagnostic = json.loads(
        (ROOT / "reports/exp167_visual_pair_error_diagnostic_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    parent_calibration = json.loads(
        (ROOT / "reports/exp172_parent_calibrator_diagnostic_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    appearance_result = json.loads(
        (ROOT / "reports/exp174_parent_appearance_rank_ensemble_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    geometry_result = json.loads(
        (ROOT / "reports/exp175_parent_geometry_rank_ensemble_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    robust_geometry = json.loads(
        (ROOT / "reports/exp178_parent_geometry_robust_calibration_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    observed_gap = json.loads(
        (RESULTS / "exp179_source/gate.json").read_text(encoding="utf-8")
    )
    deepcenter_training = json.loads(
        (ROOT / "reports/exp180_reciprocal_deepcenter_training_result_20260910.json").read_text(
            encoding="utf-8"
        )
    )
    synthetic_gap_source = json.loads(
        (RESULTS / "exp182_source_gate/results/gate.json").read_text(encoding="utf-8")
    )
    synthetic_gap_target = json.loads(
        (RESULTS / "exp185_target_oof/results/gate.json").read_text(encoding="utf-8")
    )
    prior = json.loads((ROOT / "reports/oof_stability.json").read_text(encoding="utf-8"))
    arm = "registered_hungarian"
    scratch_rows = {row["dataset"]: row for row in scratch["per_movie_by_arm"][arm]}
    zebra_rows = {row["dataset"]: row for row in zebra["per_movie_by_arm"][arm]}
    rows = []
    for dataset in scratch_rows:
        old = scratch_rows[dataset]
        new = zebra_rows[dataset]
        rows.append(
            f"| `{dataset}` | {old['adj_edge_jaccard']:.6f} | "
            f"{new['adj_edge_jaccard']:.6f} | "
            f"{new['adj_edge_jaccard'] - old['adj_edge_jaccard']:+.6f} |"
        )
    scratch_score = scratch["summary_by_arm"][arm]["score"]
    zebra_score = zebra["summary_by_arm"][arm]["score"]
    if synthetic_gap_target["status"] == "REJECT_TARGET_OOF_GATE":
        publication_status = (
            "**Publication status: RETRY BEFORE OPENING AS AN IMPROVED MODEL.** Synthetic midpoint "
            "recovery raised pooled reciprocal OOF, but failed the preregistered per-movie stability "
            "gate. The notebook is publication-worthy as a reproducible negative-result report; this "
            "candidate is not private-ready and is not eligible for a Kaggle submission."
        )
    elif locked is not None:
        publication_status = (
            "**Publication status: RETRY BEFORE OPENING AS AN IMPROVED MODEL.** The one-time locked "
            "audit rejected the transferred initializer on both embryo directions. This notebook is "
            "already useful as a reproducible negative-result report, but the model is not private-ready."
        )
    elif reciprocal is None:
        publication_status = (
            "**Publication status: HOLD.** The complete reciprocal development run is in progress; "
            "opening now would overstate one-direction evidence."
        )
    elif reciprocal["development_gate"]["gate_pass"]:
        publication_status = (
            "**Publication status: HOLD FOR LOCKED AUDIT.** Reciprocal development evidence passed, "
            "but the one-time frozen audit and hidden-runtime check are not yet complete."
        )
    else:
        publication_status = (
            "**Publication status: RETRY BEFORE OPENING.** Reciprocal development evidence did not pass "
            "the predeclared gate; the negative result is reported without claiming private readiness."
        )

    cells = [
        markdown(
            "# Biohub Cell Tracking During Development: honest embryo-level OOF\n\n"
            "**Primary target: post-close PRIVATE leaderboard performance.** Public LB is used only "
            "to verify hidden runtime and catch gross regressions; it is not the model-selection metric. "
            "Selection requires embryo-disjoint OOF, worst-fold stability, paired movie deltas and a "
            "locked audit.\n\n"
            "**Post-close PRIVATE score: not observable before the competition closes.** The honest "
            "pre-close proxy reported here is reciprocal embryo-disjoint OOF; no public score is "
            "presented as a substitute for private performance.\n\n"
            "**Current 24-movie reciprocal synthetic-gap OOF:** base `0.686231`, candidate `0.699611` "
            "(`+0.013380`). This aggregate gain did **not** pass the private-first promotion gate: "
            "8 of 24 movies regressed and the worst movie delta was `-0.014529`. Aggregate gain is "
            "not evidence of private robustness when movie-level stability fails.\n\n"
            f"{publication_status}\n\n"
            "Keywords: Biohub Cell Tracking During Development, 3D microscopy, cell lineage tracking, "
            "embryo-level OOF, temporal 3D U-Net, Hungarian tracking, private leaderboard robustness."
        ),
        markdown(
            "## What remains useful even if Kaggle score does not improve\n\n"
            "This work contributes an auditable evaluation protocol rather than a copied public notebook: "
            "official files are size-checked against the live manifest; embryos are separated between "
            "training and target evaluation; checkpoint selection stays inside the source embryo; target "
            "development and locked-audit movies are frozen before training; model initialization is the "
            "only intended change; and every checkpoint/result has a SHA-256 receipt."
        ),
        markdown(
            "## Leakage-resistant split\n\n"
            "- Source embryo `44b6`: 10 movies for fitting, 2 separate movies for checkpoint selection.\n"
            "- Target embryo `6bba`: 4 development movies used once for the paired comparison.\n"
            "- Target locked audit: 8 movies per direction, opened once only after the reciprocal gate.\n"
            "- Required reciprocal experiment: train on `6bba`, evaluate on held-out `44b6`.\n\n"
            "Movie bootstrap intervals are conditional on the sampled movies. With only two embryo "
            "domains they must not be described as population confidence intervals for unseen embryos."
        ),
        markdown(
            "## Verified official-data foundation\n\n"
            f"The remote research root contains all `{data_receipt['remote']['movies']}` official training "
            f"movies: `{data_receipt['remote']['files']:,}` files and "
            f"`{data_receipt['remote']['bytes']:,}` bytes. The audit parsed "
            f"`{data_receipt['remote']['zarr_metadata_json_files_parsed']}` Zarr-v3 metadata files and "
            "recorded a cryptographic content-tree hash for every movie. The frozen split contract SHA-256 "
            f"is `{data_receipt['artifacts']['official24_contract_sha256']}`. This makes the data and split "
            "reconstructable evidence, not an implicit local state."
        ),
        markdown(
            "## First compute-matched result (seed 314159)\n\n"
            "Both arms use five epochs, the same source split, optimizer, architecture, detector threshold "
            "(`0.985`) and registered-motion Hungarian linker. The initialized arm loads only the verified "
            "74-key U-Net payload (`0 missing, 0 unexpected`).\n\n"
            "| target movie | scratch | Zebrahub init | paired delta |\n"
            "|---|---:|---:|---:|\n" + "\n".join(rows) + "\n\n"
            f"Pooled official target-development score: **{scratch_score:.6f} → {zebra_score:.6f} "
            f"({zebra_score - scratch_score:+.6f})**. The sign is 2 positive / 2 negative movies, so the "
            "effect is promising but not stable enough to open the locked audit."
        ),
        code(
            "# Reproduce the displayed table from immutable result artifacts.\n"
            "import json\n"
            "from pathlib import Path\n\n"
            "root = Path('../outputs/research/exp130_official24_private_first')\n"
            "scratch = json.loads((root / 'scratch_registered_result.json').read_text())\n"
            "zebra = json.loads((root / 'zebrahub_registered_result.json').read_text())\n"
            "scratch['summary_by_arm']['registered_hungarian'], zebra['summary_by_arm']['registered_hungarian']"
        ),
        markdown(
            "## Repeat-seed check (seed 271828)\n\n"
            f"The exact repeat changed scratch from "
            f"`{repeat_scratch['summary_by_arm'][arm]['score']:.6f}` to "
            f"`{repeat_zebra['summary_by_arm'][arm]['score']:.6f}` with Zebrahub initialization "
            f"(`{repeat_zebra['summary_by_arm'][arm]['score'] - repeat_scratch['summary_by_arm'][arm]['score']:+.6f}`). "
            "All four movie deltas are positive. Both seeds favor initialization, but their effect sizes "
            "differ substantially; reciprocal embryo evidence remains mandatory."
        ),
        markdown(
            "## How verified open work is used\n\n"
            "Open solutions are treated as attributed mechanisms, not as frozen submissions to replay. "
            "The clean public families provide: a temporal 3D U-Net + transformer detector, a robust "
            "registered-motion Hungarian linker, a weak learned ambiguity tie-break, and a detector-diverse "
            "three-U-Net coordinate proposal. Existing honest OOF retained registered motion and only a "
            "very weak learned tie-break; heavy learned/ILP association was rejected. New mechanisms enter "
            "only through the same embryo-disjoint protocol.\n\n"
            "| frozen mechanism | held-out 44b6 | held-out 6bba | pooled 183 movies |\n"
            "|---|---:|---:|---:|\n"
            f"| registered Hungarian | {prior['embryo_folds']['44b6']['registered_score']:.6f} | "
            f"{prior['embryo_folds']['6bba']['registered_score']:.6f} | "
            f"{prior['pooled']['registered_score']:.6f} |\n"
            f"| + 10% learned tie-break | {prior['embryo_folds']['44b6']['weak_score']:.6f} | "
            f"{prior['embryo_folds']['6bba']['weak_score']:.6f} | "
            f"{prior['pooled']['weak_score']:.6f} |\n\n"
            f"The weak tie-break adds only `{prior['pooled']['weak_minus_registered']:+.6f}` pooled; this is "
            "why a four-movie gain cannot justify retuning it."
        ),
        markdown(
            "## Exact attribution of inspected open notebooks\n\n"
            "The public sources below are archived by exact version and SHA. Their title/LB labels are "
            "provenance, not private validation. We borrow testable mechanisms, not their output files "
            "or entire public-tuned presets.\n\n"
            "| source | mechanisms inspected | private-first status |\n"
            "|---|---|---|\n"
            "| `qrz1201/biohub-public-0-941-repro`, v1 | dual-seed detection, harmonic bidirectional "
            "association, registered relinking, DeepCenter/division guards | source verified; full "
            "correlated preset not admitted |\n"
            "| `tangai1/biohub-c33-public0933-v19-fallback`, v1 | secondary-detector fusion, harmonic "
            "association, ILP and short-track recovery | source verified; mechanism donor only |\n"
            "| `pilkwang/biohub-tracking-support-pack-50ep-v1` | TemporalUNet3D + transformer, graph "
            "IO/evaluation, registered-motion association | admitted only where exact runtime and OOF "
            "receipts exist |\n"
            "| `reyhanksatria/biohub-cell-tracking-0-946-lb`, snapshot last run 2026-09-08 | "
            "D4 inverse-transform averaging of U-Net edge features | exact source snapshot verified; "
            "EXP145 found exact zero effect under the coordinate-only registered linker; full public-tuned "
            "stack not admitted |\n\n"
            "Full source/code hashes, attached datasets and admission rules are recorded in "
            "`reports/OPEN_SOLUTION_PROVENANCE.md`."
        ),
        markdown(
            "## Why the public LB is secondary\n\n"
            "The earlier Zebrahub-initialized runtime notebook scored `0.616` publicly, far below the clean "
            "public frontier. That negative result is preserved. It does not answer the private-selection "
            "question because it used a different short pilot and had no reciprocal OOF. Conversely, a tiny "
            "public gain would not override a negative embryo-disjoint result."
        ),
        markdown(
            "## Fixed coordinate-consensus ensemble\n\n"
            "A verified open mechanism was tested without a hyperparameter sweep: mutual-nearest detector "
            "matches below 2 µm, fixed `alpha=0.5`, with the base registered topology preserved. The stronger "
            f"ensemble scored `{consensus['summary_by_arm']['zebrahub_topology_consensus_coords']['score']:.6f}` "
            f"versus `{zebra_score:.6f}` for its parent. Despite the pooled gain, one of four movies regressed; "
            "the predeclared stability gate failed, so this ensemble is retained as evidence rather than promoted."
        ),
        markdown(
            "## Source-selected dual-seed ensemble\n\n"
            "The topology base was selected only by source-validation score, then coordinates were averaged "
            "with the other seed using the same fixed consensus rule. It improved the selected parent from "
            f"`{repeat_zebra['summary_by_arm'][arm]['score']:.6f}` to "
            f"`{dual_seed['summary_by_arm']['scratch_topology_consensus_coords']['score']:.6f}`, but one movie "
            "changed by `-0.000644`. The strict all-movie gate therefore rejects promotion despite the positive "
            "pooled result. This distinction between exploratory promise and private-ready evidence is intentional."
        ),
        markdown(
            "## Lower learning-rate ablation\n\n"
            "Reducing fine-tuning LR from `1e-4` to `5e-5` improved every development movie and raised "
            f"pooled score to `{low_lr['summary_by_arm'][arm]['score']:.6f}`. It nevertheless reduced mean "
            f"node recall from `{repeat_zebra['summary_by_arm'][arm]['node_recall']:.6f}` to "
            f"`{low_lr['summary_by_arm'][arm]['node_recall']:.6f}`. The predeclared no-recall-regression gate "
            "therefore rejects promotion. This preserves the distinction between precision gains and robust "
            "cell recovery."
        ),
        markdown(
            "## Full-model transfer ablation\n\n"
            "All 136 checkpoint tensors matched exactly, allowing a clean test of transferring the real-Zebrahub "
            "temporal/edge head as well as the U-Net. Target score fell to "
            f"`{full_model['summary_by_arm'][arm]['score']:.6f}` while node recall rose. Large predicted-node "
            "excess triggered the official count adjustment. The conclusion is specific and reusable: retain "
            "independent visual U-Net pretraining, but re-learn temporal association on competition data."
        ),
        markdown(
            "## Discriminative learning-rate ablation\n\n"
            "A mechanism-led follow-up trained the transferred U-Net at `1e-5` while keeping the random "
            "competition-specific head at `1e-4`. Source-only checkpoint selection retained epoch 0, but "
            f"target-development score fell from `{discriminative_lr['parent_score']:.6f}` to "
            f"`{discriminative_lr['candidate_score']:.6f}` and mean node recall changed by "
            f"`{discriminative_lr['node_recall_delta']:+.6f}`. All four movies regressed. The reusable "
            "lesson is that visual pretraining helps initialization, but the U-Net still needs substantial "
            "real-domain adaptation during this short fine-tune."
        ),
        markdown(
            "## Source-only detector calibration\n\n"
            "Thresholds `[0.95, 0.97, 0.985, 0.99]` were scored only on the two source-embryo "
            "checkpoint-validation movies. That frozen selector chose `0.95` before target inference. "
            f"The one target pass improved pooled score from `{source_threshold['parent_score']:.6f}` "
            f"to `{source_threshold['candidate_score']:.6f}` and node recall by "
            f"`{source_threshold['node_recall_delta']:+.6f}`. Two movies nevertheless regressed "
            "(`-0.005583` and `-0.000325`), so the strict stability gate rejects promotion. This is "
            "promising calibration evidence, not permission to tune again on target movies.\n\n"
            "The independent seed replication selected the opposite grid end (`0.99`, not `0.95`) "
            f"and changed target score by `{source_threshold_repeat['pooled_delta']:+.6f}` with node "
            f"recall delta `{source_threshold_repeat['node_recall_delta']:+.6f}`. Thus a threshold chosen "
            "from only two source movies is seed-unstable and is not a private-ready global rule."
        ),
        markdown(
            "## Two-seed U-Net weight-soup ablation\n\n"
            "Because both fine-tunes shared one initializer, a fixed 50/50 average of their 64 floating "
            "U-Net tensors was tested while retaining the source-selected tracking head. All 136 state "
            "keys, shapes and dtypes matched, but the soup scored "
            f"`{weight_soup['source_gate']['soup_score']:.1f}` on source validation versus "
            f"`{weight_soup['source_gate']['parent_score']:.6f}` for its parent. The source gate stopped "
            "the run before target inference. Independent fine-tune paths were not linearly compatible; "
            "prediction- or coordinate-level ensembling is safer than naive weight averaging."
        ),
        markdown(
            "## Guarded dual-seed detector-logit fusion\n\n"
            "A fixed 50/50 detector-logit average borrowed from an attributed open-solution mechanism "
            "was evaluated while retaining the stronger seed's features and tracking head. A one-sided "
            "guard fell back to the primary detector only when fused proposal count dropped below 90%. "
            f"The target-development score changed from `{detector_fusion['parent_score']:.6f}` to "
            f"`{detector_fusion['candidate_score']:.6f}` "
            f"(`{detector_fusion['pooled_delta']:+.6f}`). Three of four movies regressed, including "
            f"a worst paired delta of `{min(row['delta'] for row in detector_fusion['per_movie']):+.6f}`. "
            "Node recall rose slightly, but excess proposals damaged edge precision. The guard activated "
            "on only one of 400 target frames because it controlled proposal loss but not proposal excess. "
            "This is a useful negative result: future prediction ensembles need a symmetric count or "
            "precision-aware guard, validated reciprocally rather than tuned on these target movies."
        ),
        markdown(
            "## Early reverse-embryo pipeline pilot\n\n"
            "While the remaining official files were being acquired, a pre-registered infrastructure "
            "pilot trained on five complete `6bba` movies, selected checkpoints on two separate `6bba` "
            "movies, and evaluated once on four frozen `44b6` development movies. Zebrahub U-Net "
            f"initialization changed registered score from "
            f"`{reciprocal_pilot['target_registered']['scratch_score']:.6f}` to "
            f"`{reciprocal_pilot['target_registered']['zebrahub_score']:.6f}` "
            f"(`{reciprocal_pilot['target_registered']['pooled_delta']:+.6f}`) and node recall by "
            f"`{reciprocal_pilot['target_registered']['node_recall_delta']:+.6f}`. Only two of four "
            "movie deltas were positive. This supports a directional reverse-fold signal but is not the "
            "required 10+2 reciprocal experiment and cannot justify opening locked data or submitting."
        ),
        *(
            [
                markdown(
                    "## Full reciprocal development result\n\n"
                    f"The complete 10-train + 2 source-selection reverse fold is finished. The "
                    f"predeclared reciprocal gate status is **{reciprocal['development_gate']['status']}**. "
                    f"Across both embryo directions, the pooled score delta is "
                    f"`{reciprocal['development_gate']['pooled']['delta']['score']:+.6f}` and the worst "
                    f"candidate fold score is `{reciprocal['development_gate']['worst_candidate_fold_score']:.6f}`. "
                    "All displayed aggregates were recomputed from per-movie sufficient statistics rather "
                    "than trusted from stored summaries."
                )
            ]
            if reciprocal is not None
            else [
                markdown(
                    "## Full reciprocal development result\n\n"
                    "The audited official24 corpus is complete and the 10-train + 2 source-selection reverse "
                    "fold is currently running on one leased RTX6000. No provisional score is used for "
                    "selection, and the locked audit remains unopened."
                )
            ]
        ),
        *(
            [
                markdown(
                    "## One-time locked audit: development did not generalize\n\n"
                    "All four frozen arms were completed before any locked score was read. Zebrahub "
                    "initialization changed `44b6→6bba` from "
                    f"`{locked['folds']['44b6_to_6bba']['scratch_score']:.6f}` to "
                    f"`{locked['folds']['44b6_to_6bba']['zebrahub_score']:.6f}` "
                    f"(`{locked['folds']['44b6_to_6bba']['score_delta']:+.6f}`), and `6bba→44b6` "
                    f"from `{locked['folds']['6bba_to_44b6']['scratch_score']:.6f}` to "
                    f"`{locked['folds']['6bba_to_44b6']['zebrahub_score']:.6f}` "
                    f"(`{locked['folds']['6bba_to_44b6']['score_delta']:+.6f}`). Across 16 movies, "
                    f"the official pooled score changed `{locked['pooled']['scratch_score']:.6f}` → "
                    f"`{locked['pooled']['zebrahub_score']:.6f}` "
                    f"(`{locked['pooled']['score_delta']:+.6f}`), despite node recall increasing by "
                    f"`{locked['pooled']['node_recall_delta']:+.6f}`. The robust conclusion is that "
                    "external initialization improves sensitivity but harms lineage-edge quality. It is "
                    "rejected for PRIVATE_ROBUST and receives no LB submission."
                )
            ]
            if locked is not None
            else []
        ),
        *(
            [
                markdown(
                    "## Four-view feature TTA: a mechanistically inert ablation\n\n"
                    "An attributed open solution suggested inverse-transform averaging of U-Net edge "
                    "features. Under our registered-motion production linker, both reciprocal development "
                    f"folds were bit-for-bit metric-identical to the parent (pooled delta "
                    f"`{feature_tta['development']['pooled_delta']:+.6f}`). The reason is structural: "
                    "the linker uses detector coordinates and motion, while this ablation changes only "
                    "learned edge representations. This saves future compute: feature TTA must be paired "
                    "with a learned linker to have any possible effect."
                )
            ]
            if feature_tta is not None
            else []
        ),
        *(
            [
                markdown(
                    "## Independent scratch-seed coordinate consensus\n\n"
                    "A prospectively frozen 24-movie test selected seed `314159` topology in both "
                    "directions using source-only checkpoint validation, then averaged mutual-nearest "
                    "coordinates with seed `271828` at a fixed 50/50 weight. It failed in both domains: "
                    f"`44b6→6bba` delta `{seed_consensus['folds']['44b6_to_6bba']['delta']:+.6f}` and "
                    f"`6bba→44b6` delta `{seed_consensus['folds']['6bba_to_44b6']['delta']:+.6f}`; pooled "
                    f"`{seed_consensus['pooled']['parent_score']:.6f}` → "
                    f"`{seed_consensus['pooled']['candidate_score']:.6f}` "
                    f"(`{seed_consensus['pooled']['delta']:+.6f}`). The stratified movie-bootstrap 95% "
                    f"interval was `[{seed_consensus['uncertainty']['score_delta_percentile_95'][0]:+.6f}, "
                    f"{seed_consensus['uncertainty']['score_delta_percentile_95'][1]:+.6f}]`, with only "
                    f"`{100 * seed_consensus['uncertainty']['probability_delta_positive']:.2f}%` positive "
                    "draws. Every leave-one-movie-out pooled delta remained negative. This is stable "
                    "evidence against unconditional coordinate averaging, not a near-tie to submit."
                )
            ]
            if seed_consensus is not None
            else []
        ),
        *(
            [
                markdown(
                    "## Attributed conservative division repair\n\n"
                    "The registered linker is one-to-one, so an attributed geometric `safe_division` "
                    "core from `qrz1201/biohub-public-0-941-repro` was isolated and tested without a "
                    "DeepCenter veto. The edge component moved slightly upward "
                    f"(`{safe_division['pooled']['score_delta']:+.6f}`), but the repair recovered "
                    f"`{safe_division['pooled']['division_tp_delta']}` true divisions and created "
                    f"`{safe_division['pooled']['division_fp_delta']}` false division parents; measured "
                    f"division precision was `{safe_division['pooled']['division_precision']:.3f}`. "
                    "It is rejected. Geometry alone is not a credible fork detector for this model; the "
                    "next division-aware attempt needs a learned signal or an independently validated veto."
                )
            ]
            if safe_division is not None
            else []
        ),
        markdown(
            "## Learned-linker and native-ILP diagnostics\n\n"
            "Feature TTA under the weak learned linker moved only one of four forward movies "
            f"(`{weak_feature_tta['forward']['pooled_score_delta']:+.6f}`) and was exactly inert "
            f"in the reciprocal direction (`{weak_feature_tta['reverse']['pooled_score_delta']:+.6f}`), "
            "so it was not promoted. Raw native ILP then failed closed at out-degree 3 before a "
            "complete score existed. A source-attributed geometry cap made it valid but exposed the "
            "main issue: the native graph is far too sparse and changed pooled score by "
            f"`{native_geometry['pooled']['score_delta']:+.6f}` with zero division TP. Finally, using "
            "those sparse edges only as add-only second-daughter evidence accepted "
            f"`{native_guided['accepted_divisions_forward'] + native_guided['accepted_divisions_reverse']}` "
            "divisions and changed score by exactly zero. These negative controls motivate source-only "
            "selection of a denser learned edge pool; they do not authorize an LB submission."
        ),
        markdown(
            "## Source-selected dense learned-edge pool\n\n"
            "EXP152 lowered the native-edge cutoff from `0.5` as far as `0.02`, but selected it only "
            "from the two source checkpoint-validation movies in each direction. Every threshold was "
            "exactly inert on both source folds, so the conservative tie-break retained `0.5`. The "
            "prospective 24-movie target evaluation then changed pooled score from "
            f"`{dense_native['prospective_target_oof']['pooled_parent_score']:.6f}` to "
            f"`{dense_native['prospective_target_oof']['pooled_candidate_score']:.6f}` "
            f"(`{dense_native['prospective_target_oof']['pooled_score_delta']:+.6f}`), with zero "
            "division-TP or recall change. This closes the threshold-only branch and points to a "
            "division-aware training or proposal change, not another target-tuned cutoff."
        ),
        markdown(
            "## External division-head diagnostic\n\n"
            "The frozen official split audit exposed only one division parent in 44b6 training and none "
            "in its checkpoint-selection movies, versus 11+1 in 6bba. We therefore tested the existing "
            "real-Zebrahub head on its independent 64-shard time validation before spending compute on "
            "retraining. At threshold `0.5`, division-parent recall was "
            f"`{division_signal['threshold_0_5']['division_parent_recall']:.3f}` with precision "
            f"`{division_signal['threshold_0_5']['division_parent_precision']:.3f}`; at `0.2`, recall rose "
            f"to `{division_signal['threshold_0_2']['division_parent_recall']:.3f}` but precision fell to "
            f"`{division_signal['threshold_0_2']['division_parent_precision']:.3f}`. This is external "
            "mechanism evidence, not competition OOF. It says the head contains a fork signal, but transfer "
            "needs a high-precision veto and must preserve the robust scratch detector/topology."
        ),
        markdown(
            "## Prospective external-score transfer tests\n\n"
            "EXP154 scored fixed scratch coordinates with the immutable real-Zebrahub edge head. "
            f"Across 24 prospective target movies, pooled score changed from "
            f"`{external_edge['pooled_parent_score']:.6f}` to "
            f"`{external_edge['pooled_candidate_score']:.6f}` "
            f"(`{external_edge['pooled_score_delta']:+.6f}`), and both embryo directions were positive. "
            f"However, it recovered `{external_edge['division_tp_delta']}` of 13 true division parents "
            f"and introduced `{external_edge['division_fp_delta']}` false forks, so the division gate "
            "rejected it. EXP155 then isolated the ordinary-edge interpretation as a strict one-to-one "
            "tie-break. It failed before target evaluation: forward source deltas were "
            f"`{external_weak['candidates'][0]['score_delta']:+.6f}` and "
            f"`{external_weak['candidates'][1]['score_delta']:+.6f}`. These results retain the target "
            "folds for confidence-gated variants and prevent a tiny pooled gain from being mislabeled "
            "as private-ready evidence. EXP156 preserved the parent score and rejection threshold, but "
            f"still failed source-only in the reciprocal direction "
            f"(`{external_confidence['reverse']['best_score_delta']:+.6f}`). EXP157 then retrained only the "
            "external temporal transformer with explicit division-positive weighting. External division "
            f"F1 improved by `{division_recalibration['external_gate']['division_f1_delta']:+.6f}`, yet "
            "its 24-movie competition result was identical to EXP154: zero true divisions and "
            f"`{division_recalibration['prospective_target_oof']['division_fp_delta']}` false forks. "
            "Loss reweighting alone is therefore insufficient. EXP159 changed the representation to "
            "an explicit daughter-symmetric visual pair classifier. Its external proposal pool covered "
            f"`{visual_pair['external_validation']['covered_true_pairs']}` of "
            f"`{visual_pair['external_validation']['division_parents']}` division parents and pair AP was "
            f"`{visual_pair['external_validation']['pair_average_precision']:.6f}`, but at precision "
            f"`{visual_pair['external_validation']['precision']:.2f}` recall was only "
            f"`{visual_pair['external_validation']['recall']:.3f}`. It failed externally, so no competition "
            "fold was opened. Frozen pretrained visual features improved the best observed recall at "
            f"precision above 0.50 to `{pretrained_pair['best_observed_high_precision_recall']['recall']:.3f}`. "
            "The preregistered equal-rank ensemble reached precision/recall "
            f"`{pair_ensemble['external_validation']['precision']:.2f}/"
            f"{pair_ensemble['external_validation']['recall']:.3f}` with component correlation "
            f"`{pair_ensemble['external_validation']['component_score_correlation']:.3f}`, still below "
            "the 0.20 recall gate. This separates proposal coverage from ranking quality and records a "
            "reproducible negative result without spending a leaderboard slot."
        ),
        markdown(
            "## What the daughter-pair diagnostic changed\n\n"
            "EXP167 separated candidate ranking from division-parent calibration on the frozen external "
            "time-validation set. Among covered true divisions, the correct pair ranked first for "
            f"`{pair_diagnostic['top_pair_recall']['scratch']:.1%}` with the scratch visual head and "
            f"`{pair_diagnostic['top_pair_recall']['pretrained_feature']:.1%}` with frozen pretrained "
            "features. Yet their precision-0.50 operating points recovered only "
            f"`{pair_diagnostic['operating_points']['scratch']}` and "
            f"`{pair_diagnostic['operating_points']['pretrained_feature']}` true/predicted parents; "
            f"the fixed ensemble reached `{pair_diagnostic['operating_points']['equal_rank_ensemble']}`. "
            "The next model therefore needs a separately fitted division-propensity head and hard "
            "ordinary negatives, rather than another daughter-pair search heuristic. This is external mechanism "
            "evidence, not embryo-level competition OOF or an estimate of the post-close private score."
        ),
        markdown(
            "## Honest threshold transport: the result that changes the plan\n\n"
            "EXP171 trained a flexible parent-propensity MLP, but EXP172 showed that it damaged the raw "
            f"pair ordering: prospective parent AP fell from `{parent_calibration['prospective']['raw_parent_ap']:.6f}` "
            f"to `{parent_calibration['prospective']['mlp_parent_ap']:.6f}`. A regularized parent-appearance "
            f"head was also non-transferable (prospective AP `{appearance_result['prospective']['appearance_ap']:.6f}`). "
            "EXP175 then isolated five explicit pair-geometry features. Geometry improved prospective AP to "
            f"`{geometry_result['geometry']['prospective_ap']:.6f}`; the fixed pair-plus-geometry blend reached "
            f"recall `{geometry_result['blend']['prospective_recall']:.3f}`. Crucially, its threshold was selected "
            "on calibration only and transferred unchanged. Prospective precision was only "
            f"`{geometry_result['blend']['prospective_precision']:.3f}`, below the frozen 0.50 gate. Selecting a "
            "new threshold on this already observed prospective window would be leakage. The retained value is "
            "therefore a verified mechanism and a stricter evaluation lesson, not a promoted model. "
            "A fresh four-block nested calibration then failed on every held block; held precision/recall was "
            f"`{robust_geometry['held_blocks'][0]['precision']:.3f}/{robust_geometry['held_blocks'][0]['recall']:.3f}`, "
            f"`{robust_geometry['held_blocks'][1]['precision']:.3f}/{robust_geometry['held_blocks'][1]['recall']:.3f}`, "
            f"`{robust_geometry['held_blocks'][2]['precision']:.3f}/{robust_geometry['held_blocks'][2]['recall']:.3f}`, and "
            f"`{robust_geometry['held_blocks'][3]['precision']:.3f}/{robust_geometry['held_blocks'][3]['recall']:.3f}`. "
            "No statistically protected threshold existed, so official-24 remained unopened."
        ),
        markdown(
            "## Attributed open mechanism: density-aware gap closure\n\n"
            "Instead of cloning the correlated QRZ public stack, EXP179 isolated its density-aware one-frame "
            "gap rule and allowed only reuse of an already observed isolated middle-frame detection. The "
            "adaptive threshold changed endpoint eligibility, but the frozen 3.2 um middle-node condition "
            "accepted no repair in any source-validation movie. Consequently fixed, adaptive and parent scores "
            f"were identical: `{observed_gap['directions']['44b6_source']['base_score']:.6f}` on `44b6` and "
            f"`{observed_gap['directions']['6bba_source']['base_score']:.6f}` on `6bba`. The source gate was "
            f"**{observed_gap['status']}**, so official-24 remained unopened. This negative ablation shows that "
            "any value from the complete public gap mechanism must come from synthetic midpoint recovery and/or "
            "DeepCenter confirmation, not reuse of observed isolated detections."
        ),
        markdown(
            "## Leakage-controlled DeepCenter and synthetic midpoint recovery\n\n"
            "The archived public DeepCenter manifest includes every `44b6` movie, including the two "
            "movies used by our source gate. Reusing that teacher would leak validation images. EXP180 "
            "therefore trained two independent source-only models from explicit, disjoint 10-train/2-"
            "checkpoint-validation manifests. Their epoch-2 validation losses were "
            f"`{deepcenter_training['folds']['44b6']['epoch_2_validation_loss']:.6f}` on `44b6` and "
            f"`{deepcenter_training['folds']['6bba']['epoch_2_validation_loss']:.6f}` on `6bba`; exact "
            "checkpoint hashes and cleanup evidence are preserved in the EXP180 receipt. "
            "EXP182 then evaluated the attributed QRZ synthetic-midpoint mechanism on the two "
            "held-out source movies in each embryo. Its frozen two-embryo source gate was "
            f"**{synthetic_gap_source['status']}**: score improved by "
            f"`{synthetic_gap_source['directions']['44b6_source']['deepcenter_minus_base']:+.6f}` on "
            f"`44b6` and `{synthetic_gap_source['directions']['6bba_source']['deepcenter_minus_base']:+.6f}` "
            "on `6bba`, with no movie-level score or recall regression. EXP185 then performed the "
            "preregistered reciprocal target evaluation over all 24 movies. Pooled score improved from "
            f"`{synthetic_gap_target['pooled']['base_score']:.6f}` to "
            f"`{synthetic_gap_target['pooled']['deepcenter_score']:.6f}` "
            f"(`{synthetic_gap_target['pooled']['deepcenter_minus_base']:+.6f}`), and recall never "
            "decreased, but 8 of 24 movies lost score. The worst loss was "
            f"`{synthetic_gap_target['pooled']['worst_movie_score_delta']:+.6f}`. The frozen target gate "
            f"therefore returned **{synthetic_gap_target['status']}**. This is a concrete example of why "
            "an attractive pooled gain cannot substitute for paired movie-level stability; the candidate "
            "is not private-ready and no Kaggle submission is authorized."
        ),
        markdown(
            "## Next decision gate\n\n"
            "1. Use scratch, not external initialization, as the robust parent.\n"
            "2. Do not use unconditional coordinate averaging; EXP146 rejected it robustly.\n"
            "3. Do not promote the current geometry calibrator; nested blocks failed its protected-precision gate.\n"
            "4. Report embryo-direction, per-movie and pooled official metrics; do not reuse the consumed locked "
            "audit as if it were untouched.\n"
            "5. Do not submit the current synthetic-gap family: EXP182 passed its source gate, but EXP185 failed "
            "the frozen target stability gate despite a positive pooled delta.\n"
            "6. Treat the EXP185 target labels as consumed. Any follow-up on this family is exploratory unless "
            "it uses a new source-only or properly nested protocol; it must not be called untouched confirmatory OOF.\n"
            "7. Build an Internet-off runtime-inference Kaggle notebook only after a new candidate passes its "
            "local evidence gate; no LB slot is justified by EXP185.\n"
            "8. Open this notebook as an improved-model solution only after its header accurately distinguishes "
            "measured OOF, public LB "
            "and the still-unobservable post-close private score."
        ),
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
