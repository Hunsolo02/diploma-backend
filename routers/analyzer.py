from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from config import settings
from analyzer.tui import analyze_face_landmarks

router = APIRouter(prefix="/analyze", tags=["analyze"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/landmarks")
async def analyze_landmarks(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WebP)"),
):
    """
    Accept an image file, detect face landmarks, and return points + optional annotated image.
    """
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    result = analyze_face_landmarks(
        image_bytes=image_bytes,
        weights_path=settings.LANDMARK_WEIGHTS_PATH,
        draw_points=True,
        return_image_base64=True,
    )

    if result["error"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return {
        "points": result["points"],
        "annotated_image_base64": result["annotated_image_base64"],
    }


@router.post("/landmarks/bytes")
async def analyze_landmarks_bytes(request: Request):
    """
    Accept raw image bytes in request body (Content-Type: image/jpeg, image/png, etc.).
    """
    content_type = request.headers.get("content-type", "")
    if not any(ct in content_type for ct in ("image/jpeg", "image/png", "image/webp")):
        raise HTTPException(
            status_code=400,
            detail="Content-Type must be image/jpeg, image/png, or image/webp",
        )
    image_bytes = await request.body()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty body")

    result = analyze_face_landmarks(
        image_bytes=image_bytes,
        weights_path=settings.LANDMARK_WEIGHTS_PATH,
        draw_points=True,
        return_image_base64=True,
    )

    if result["error"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return {
        "points": result["points"],
        "annotated_image_base64": result["annotated_image_base64"],
    }
