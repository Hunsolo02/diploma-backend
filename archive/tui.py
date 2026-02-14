"""Face landmark analyzer - can be used from backend or CLI."""
import base64
import io
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw
from torchvision import transforms
import mediapipe as mp

from .model import LandmarkModel

IMG_SIZE = 128
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Cached model (lazy-loaded on first call)
_model_cache: dict[str, tuple[LandmarkModel, int]] = {}


def get_transform():
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def load_num_points_from_weights(state: dict) -> int:
    if "base.fc.weight" in state:
        out_features = state["base.fc.weight"].shape[0]
    else:
        out_features = max(
            v.shape[0] for v in state.values()
            if isinstance(v, torch.Tensor) and v.ndim == 2
        )
    if out_features % 2 != 0:
        raise RuntimeError(f"Unexpected out_features={out_features}")
    return out_features // 2


def pred_to_points(pred_np: np.ndarray, num_points: int) -> np.ndarray:
    if pred_np.ndim == 3:
        pts = pred_np[0]
    else:
        pts = pred_np[0].reshape(num_points, 2)
    return pts.astype(np.float32)


def detect_face_bbox(pil_img: Image.Image) -> tuple[int, int, int, int] | None:
    img_rgb = np.array(pil_img.convert("RGB"))
    h, w = img_rgb.shape[:2]

    mp_fd = mp.solutions.face_detection
    with mp_fd.FaceDetection(model_selection=1, min_detection_confidence=0.5) as fd:
        res = fd.process(img_rgb)

    if not res.detections:
        return None

    det = max(res.detections, key=lambda d: d.score[0])
    box = det.location_data.relative_bounding_box

    x0 = int(box.xmin * w)
    y0 = int(box.ymin * h)
    bw = int(box.width * w)
    bh = int(box.height * h)
    x1 = x0 + bw
    y1 = y0 + bh

    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(w - 1, x1)
    y1 = min(h - 1, y1)
    return x0, y0, x1, y1


def make_square_bbox(x0: int, y0: int, x1: int, y1: int, W: int, H: int, scale: float = 1.35) -> tuple[int, int, int, int]:
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    bw = x1 - x0
    bh = y1 - y0
    side = max(bw, bh) * scale

    nx0 = int(cx - side / 2)
    ny0 = int(cy - side / 2)
    nx1 = int(cx + side / 2)
    ny1 = int(cy + side / 2)

    nx0 = max(0, nx0)
    ny0 = max(0, ny0)
    nx1 = min(W - 1, nx1)
    ny1 = min(H - 1, ny1)
    return nx0, ny0, nx1, ny1


def draw_points(img: Image.Image, pts_xy: np.ndarray, r: int = 4) -> Image.Image:
    out = img.copy()
    d = ImageDraw.Draw(out)
    for x, y in pts_xy:
        x, y = float(x), float(y)
        d.ellipse((x - r, y - r, x + r, y + r), fill="red", outline="red")
    return out


def _get_model(weights_path: str) -> tuple[LandmarkModel, int]:
    """Load and cache model by weights path."""
    if weights_path in _model_cache:
        return _model_cache[weights_path]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    state = torch.load(weights_path, map_location=device)
    num_points = load_num_points_from_weights(state)
    model = LandmarkModel(num_points).to(device)
    model.load_state_dict(state)
    model.eval()
    _model_cache[weights_path] = (model, num_points)
    return model, num_points


def analyze_face_landmarks(
    image_bytes: bytes,
    weights_path: str,
    draw_points: bool = True,
    return_image_base64: bool = True,
) -> dict[str, Any]:
    """
    Analyze face landmarks from image bytes.

    Args:
        image_bytes: Raw image bytes (JPEG, PNG, etc.)
        weights_path: Path to model weights (.pth)
        draw_points: Whether to draw landmark points on the image
        return_image_base64: Whether to include annotated image as base64 in response

    Returns:
        dict with:
            - points: list of [x, y] coordinates in original image space
            - annotated_image_base64: base64 string (if return_image_base64)
            - error: error message if failed
    """
    result: dict[str, Any] = {"points": [], "annotated_image_base64": None, "error": None}
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        result["error"] = f"Invalid image: {e}"
        return result

    W, H = img.size
    bbox = detect_face_bbox(img)
    if bbox is None:
        result["error"] = "Face not detected"
        return result

    x0, y0, x1, y1 = make_square_bbox(*bbox, W, H, scale=1.35)
    face_crop = img.crop((x0, y0, x1, y1))
    crop_w, crop_h = face_crop.size

    model, num_points = _get_model(weights_path)
    device = next(model.parameters()).device
    x = get_transform()(face_crop).unsqueeze(0).to(device)

    with torch.no_grad():
        pred = model(x)

    pred_np = pred.detach().cpu().numpy()
    pts_model = pred_to_points(pred_np, num_points)

    pts_crop_px = pts_model.copy()
    pts_crop_px[:, 0] *= crop_w
    pts_crop_px[:, 1] *= crop_h

    pts_orig = pts_crop_px.copy()
    pts_orig[:, 0] += x0
    pts_orig[:, 1] += y0
    pts_orig[:, 0] = np.clip(pts_orig[:, 0], 0, W - 1)
    pts_orig[:, 1] = np.clip(pts_orig[:, 1], 0, H - 1)

    result["points"] = pts_orig.tolist()

    if draw_points and return_image_base64:
        out_img = draw_points(img, pts_orig, r=4)
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        result["annotated_image_base64"] = base64.b64encode(buf.getvalue()).decode("utf-8")

    return result


def main() -> None:
    """CLI entry point - uses hardcoded paths for backward compatibility."""
    import os

    WEIGHTS_PATH = os.environ.get("LANDMARK_WEIGHTS", "/home/ermakov/webproj/trainModel2/landmark_model.pth")
    IMAGE_PATH = os.environ.get("LANDMARK_IMAGE", "/home/ermakov/photo_2025-01-28_11-14-41.jpg")
    OUT_DIR = os.environ.get("LANDMARK_OUT_DIR", "/home/ermakov/webproj/trainModel2/preds")
    OUT_NAME = "result_with_points2.png"

    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()

    result = analyze_face_landmarks(image_bytes, WEIGHTS_PATH)
    if result["error"]:
        raise SystemExit(f"❌ {result['error']}")

    print(f"✅ Detected {len(result['points'])} landmarks")
    if result.get("annotated_image_base64"):
        os.makedirs(OUT_DIR, exist_ok=True)
        out_path = os.path.join(OUT_DIR, OUT_NAME)
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(result["annotated_image_base64"]))
        print("✅ Saved:", out_path)


if __name__ == "__main__":
    main()
