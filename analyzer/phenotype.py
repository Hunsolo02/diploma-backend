"""Phenotype classification using YOLO (Ultralytics)."""
import io
from pathlib import Path
from typing import Any

from ultralytics import YOLO

_model_cache: YOLO | None = None


def _get_model(weights_path: str) -> YOLO:
    """Load and cache YOLO model."""
    global _model_cache
    if _model_cache is None:
        path = Path(weights_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / weights_path
        _model_cache = YOLO(str(path))
    return _model_cache


def predict_phenotype(
    image: bytes | str | Path,
    weights_path: str,
) -> dict[str, Any]:
    """
    Classify phenotype from image using YOLO.

    Args:
        image: Image as bytes, file path, or Path
        weights_path: Path to best.pt weights file

    Returns:
        dict with:
            - names: {class_id: class_name}
            - probs: list of probabilities per class
            - top1: predicted class name
            - top1_conf: confidence (0..1)
            - top1_idx: class index
    """
    model = _get_model(weights_path)

    if isinstance(image, bytes):
        # YOLO accepts file path or numpy array; for bytes use temporary or PIL
        import numpy as np
        from PIL import Image
        pil_img = Image.open(io.BytesIO(image)).convert("RGB")
        img_array = np.array(pil_img)
        results = model(img_array)
    else:
        results = model(str(image))

    r = results[0]
    names_dict = r.names
    probs = r.probs.data.tolist()
    top1_idx = r.probs.top1
    top1_conf = r.probs.top1conf
    if hasattr(top1_conf, "item"):
        top1_conf = top1_conf.item()

    return {
        "names": names_dict,
        "probs": [round(p, 4) for p in probs],
        "top1": names_dict[top1_idx],
        "top1_conf": round(float(top1_conf), 4),
        "top1_idx": int(top1_idx),
    }
