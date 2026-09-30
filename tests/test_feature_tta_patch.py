import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "research" / "exp145_feature_tta_source"
PARENT = SOURCE / "predict_unet_transformer_parent.py"
CANDIDATE = SOURCE / "predict_unet_transformer_feature_tta.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_feature_tta_sources_are_pinned_and_compile() -> None:
    assert digest(PARENT) == "f698f97c6b00ec92e41aec032bf24d317d565d4f14bab56610f7d4697c441d70"
    assert digest(CANDIDATE) == "4b6698ad7cfa8d7bc243107feb8783427ac01a2f76b77096c374e909eec3c4b1"
    source = CANDIDATE.read_text(encoding="utf-8")
    compile(source, str(CANDIDATE), "exec")
    assert "unet_acc = unet_out.clone()" in source
    assert "unet_acc = unet_acc + unet_flip.flip(dims)" in source
    assert "unet_out = unet_acc / 4" in source
    assert "det_logits[f] = det_logits[f] / 4" in source
