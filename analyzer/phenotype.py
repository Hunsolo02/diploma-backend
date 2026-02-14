"""Phenotype analysis: YOLO classification + Face Mesh measurements (test.py logic)."""
import io
import math
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
from ultralytics import YOLO

# --- Face Mesh constants (from test.py) ---
REFERENCE_START, REFERENCE_END = 9, 152
FOREHEAD_TOP_CANDIDATES = [10, 67, 109, 103, 297, 338, 332, 284, 251]
FACE_CHIN_INDEX = 152
FACE_WIDTH_IDX = (137, 366)
FACE_RATIO_EURYPROSOPIA_MIN = 88.0
FACE_RATIO_MESOPROSOPIA_MIN, FACE_RATIO_MESOPROSOPIA_MAX = 84.0, 87.9
NOSE_WIDTH_IDX, NOSE_LENGTH_IDX = (48, 278), (8, 94)
NOSE_TYPE_LEPTORHINIA_MAX = 69.9
NOSE_TYPE_MESORHINIA_MIN, NOSE_TYPE_MESORHINIA_MAX = 70.0, 84.9
NOSE_TYPE_CHAMAERHINIA_MIN, NOSE_TYPE_CHAMAERHINIA_MAX = 85.0, 99.0
JAW_WIDTH_IDX = (172, 397)
JAW_NARROW_REF, JAW_WIDE_REF = 0.7303, 0.8943
JAW_MARGIN = 0.05
LIP_LENGTH_IDX = (0, 17)
LIP_THIN_REF, LIP_THICK_REF = 0.0977, 0.1989
LIP_MARGIN = 0.02
CONNECTIONS_BASE = [
    (9, 152, "Длина лица"),
    (137, 366, "Ширина лица"),
    (48, 278, "Ширина носа"),
    (8, 94, "Длина носа"),
    (0, 17, "Длина губ"),
    (172, 397, "Ширина челюсти"),
]
MAX_IMAGE_DIMENSION = 1024

_yolo_model_cache: YOLO | None = None
_face_mesh: mp.solutions.face_mesh.FaceMesh | None = None


def _get_yolo_model(weights_path: str) -> YOLO:
    global _yolo_model_cache
    if _yolo_model_cache is None:
        path = Path(weights_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / weights_path
        _yolo_model_cache = YOLO(str(path))
    return _yolo_model_cache


def _get_face_mesh() -> mp.solutions.face_mesh.FaceMesh:
    global _face_mesh
    if _face_mesh is None:
        _face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
        )
    return _face_mesh


def _normalize_image(img: np.ndarray, max_dimension: int = MAX_IMAGE_DIMENSION) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) <= max_dimension:
        return img
    scale = max_dimension / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)


def _calculate_distance(lm1, lm2, img_width: int, img_height: int) -> float:
    x1 = lm1.x * img_width
    y1 = lm1.y * img_height
    x2 = lm2.x * img_width
    y2 = lm2.y * img_height
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _normalize_by_face_length(distance_px: float, reference_px: float) -> float:
    return distance_px / reference_px if reference_px > 0 else 0.0


def _image_to_array(image: bytes | str | Path) -> np.ndarray:
    """Convert image input to RGB numpy array."""
    if isinstance(image, bytes):
        pil_img = Image.open(io.BytesIO(image)).convert("RGB")
        return np.array(pil_img)
    img = Image.open(str(image)).convert("RGB")
    return np.array(img)


def analyze_face_mesh(image: bytes | str | Path) -> dict[str, Any]:
    """
    Analyze face using MediaPipe Face Mesh (logic from test.py).
    Returns JSON with measurements, face/nose/jaw/lip types.

    Args:
        image: Image as bytes, file path, or Path

    Returns:
        dict with measurements, face_type, nose_type, jaw_type, lip_type, error
    """
    img = _image_to_array(image)
    img = _normalize_image(img)
    img_height, img_width, _ = img.shape

    face_mesh = _get_face_mesh()
    results = face_mesh.process(img)

    out: dict[str, Any] = {
        "measurements": [],
        "face_type": None,
        "face_ratio_pct": None,
        "nose_type": None,
        "nose_ratio_pct": None,
        "jaw_type": None,
        "jaw_width_norm": None,
        "lip_type": None,
        "lip_length_norm": None,
        "error": None,
    }

    if not results.multi_face_landmarks:
        out["error"] = "Face not detected"
        return out

    face_landmarks = results.multi_face_landmarks[0]
    ref_start = face_landmarks.landmark[REFERENCE_START]
    ref_end = face_landmarks.landmark[REFERENCE_END]
    reference_px = _calculate_distance(ref_start, ref_end, img_width, img_height)

    # Measurements
    for start_idx, end_idx, comment in CONNECTIONS_BASE:
        start_lm = face_landmarks.landmark[start_idx]
        end_lm = face_landmarks.landmark[end_idx]
        dist_px = _calculate_distance(start_lm, end_lm, img_width, img_height)
        dist_norm = _normalize_by_face_length(dist_px, reference_px)
        out["measurements"].append({"comment": comment, "value": round(dist_norm, 4)})

    # Face type
    forehead_top_idx = min(
        FOREHEAD_TOP_CANDIDATES,
        key=lambda i: face_landmarks.landmark[i].y,
    )
    pt_top = face_landmarks.landmark[forehead_top_idx]
    pt_chin = face_landmarks.landmark[FACE_CHIN_INDEX]
    face_length_px = _calculate_distance(pt_top, pt_chin, img_width, img_height)
    fw_start, fw_end = FACE_WIDTH_IDX[0], FACE_WIDTH_IDX[1]
    face_width_px = _calculate_distance(
        face_landmarks.landmark[fw_start],
        face_landmarks.landmark[fw_end],
        img_width,
        img_height,
    )
    face_ratio_pct = (face_width_px / face_length_px * 100.0) if face_length_px > 0 else 0
    out["face_ratio_pct"] = round(face_ratio_pct, 1)
    if face_ratio_pct >= FACE_RATIO_EURYPROSOPIA_MIN:
        out["face_type"] = "Юрипросопия"
    elif FACE_RATIO_MESOPROSOPIA_MIN <= face_ratio_pct <= FACE_RATIO_MESOPROSOPIA_MAX:
        out["face_type"] = "Мезопросопия"
    else:
        out["face_type"] = "Лепторосопия"

    # Nose type
    w_start, w_end = NOSE_WIDTH_IDX[0], NOSE_WIDTH_IDX[1]
    len_start, len_end = NOSE_LENGTH_IDX[0], NOSE_LENGTH_IDX[1]
    nose_width_px = _calculate_distance(
        face_landmarks.landmark[w_start],
        face_landmarks.landmark[w_end],
        img_width,
        img_height,
    )
    nose_length_px = _calculate_distance(
        face_landmarks.landmark[len_start],
        face_landmarks.landmark[len_end],
        img_width,
        img_height,
    )
    nose_width_norm = _normalize_by_face_length(nose_width_px, reference_px)
    nose_length_norm = _normalize_by_face_length(nose_length_px, reference_px)
    nose_ratio_pct = (nose_width_norm / nose_length_norm) * 100 if nose_length_norm > 0 else 0
    out["nose_ratio_pct"] = round(nose_ratio_pct, 1)
    if nose_ratio_pct <= NOSE_TYPE_LEPTORHINIA_MAX:
        out["nose_type"] = "Лепториния"
    elif NOSE_TYPE_MESORHINIA_MIN <= nose_ratio_pct <= NOSE_TYPE_MESORHINIA_MAX:
        out["nose_type"] = "Мизориния"
    elif NOSE_TYPE_CHAMAERHINIA_MIN <= nose_ratio_pct <= NOSE_TYPE_CHAMAERHINIA_MAX:
        out["nose_type"] = "Хамэриния"
    else:
        out["nose_type"] = f"вне диапазона (>{NOSE_TYPE_CHAMAERHINIA_MAX:.0f}%)"

    # Jaw type
    j_start, j_end = JAW_WIDTH_IDX[0], JAW_WIDTH_IDX[1]
    jaw_width_px = _calculate_distance(
        face_landmarks.landmark[j_start],
        face_landmarks.landmark[j_end],
        img_width,
        img_height,
    )
    jaw_width_norm = _normalize_by_face_length(jaw_width_px, reference_px)
    narrow_bound = JAW_NARROW_REF + JAW_MARGIN
    wide_bound = JAW_WIDE_REF - JAW_MARGIN
    out["jaw_width_norm"] = round(jaw_width_norm, 4)
    if jaw_width_norm <= narrow_bound:
        out["jaw_type"] = "Узкая челюсть"
    elif jaw_width_norm >= wide_bound:
        out["jaw_type"] = "Широкая челюсть"
    else:
        out["jaw_type"] = "Средняя челюсть"

    # Lip type
    lip_start, lip_end = LIP_LENGTH_IDX[0], LIP_LENGTH_IDX[1]
    lip_length_px = _calculate_distance(
        face_landmarks.landmark[lip_start],
        face_landmarks.landmark[lip_end],
        img_width,
        img_height,
    )
    lip_length_norm = _normalize_by_face_length(lip_length_px, reference_px)
    lip_thin_bound = LIP_THIN_REF + LIP_MARGIN
    lip_thick_bound = LIP_THICK_REF - LIP_MARGIN
    out["lip_length_norm"] = round(lip_length_norm, 4)
    if lip_length_norm <= lip_thin_bound:
        out["lip_type"] = "Тонкие губы"
    elif lip_length_norm >= lip_thick_bound:
        out["lip_type"] = "Толстые губы"
    else:
        out["lip_type"] = "Средние губы"

    return out


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
        dict with: names, probs, top1, top1_conf, top1_idx
    """
    model = _get_yolo_model(weights_path)

    if isinstance(image, bytes):
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


def analyze_phenotype_full(
    image: bytes | str | Path,
    weights_path: str,
) -> dict[str, Any]:
    """
    Full phenotype analysis: YOLO classification + Face Mesh measurements.
    Single method for API use.

    Args:
        image: Image as bytes, file path, or Path
        weights_path: Path to YOLO best.pt weights

    Returns:
        JSON dict with yolo (classification) and face_mesh (measurements, types)
    """
    yolo_result = predict_phenotype(image, weights_path)
    mesh_result = analyze_face_mesh(image)
    return {
        "yolo": yolo_result,
        "face_mesh": mesh_result,
    }
