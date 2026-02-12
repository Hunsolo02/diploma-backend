import base64
import re

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from config import settings
from analyzer.tui import analyze_face_landmarks
from database import get_db
from models.analysis_question import AnalysisQuestion
from models.analysis_session import AnalysisSession
from schemas.analysis import AnalyzeRequest, AnalyzeResponse, AnalysisQuestionSchema, SubmitAnswersRequest

router = APIRouter(prefix="/analyze", tags=["analyze"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Default questions when DB has none (per MODELS_AND_FILES.md)
DEFAULT_QUESTIONS = [
    {"id": "skin_type", "label": "Тип кожи", "type": "select", "options": ["сухая", "жирная", "комбинированная", "нормальная"]},
    {"id": "reaction", "label": "Реакция на солнце", "type": "select", "options": ["обгораю легко", "загораю постепенно", "загораю хорошо"]},
    {"id": "notes", "label": "Дополнительные наблюдения", "type": "text", "options": None},
]


def _parse_data_url(data_url: str) -> bytes:
    """Extract base64 image bytes from data URL (data:image/xxx;base64,...)."""
    match = re.match(r"data:image/[^;]+;base64,(.+)", data_url, re.DOTALL)
    if not match:
        raise ValueError("Invalid data URL format. Expected: data:image/xxx;base64,...")
    return base64.b64decode(match.group(1))


def _get_questions(db: Session) -> list[AnalysisQuestionSchema]:
    """Get questions from DB or return defaults."""
    questions = db.query(AnalysisQuestion).order_by(AnalysisQuestion.id).all()
    if questions:
        return [
            AnalysisQuestionSchema(id=str(q.id), label=q.label, type=q.type, options=q.options)
            for q in questions
        ]
    return [AnalysisQuestionSchema(**q) for q in DEFAULT_QUESTIONS]


def _build_result_from_answers(answers: dict) -> dict:
    """Build result object from answers (phenotype, origin, concentration, recommendations, summary)."""
    return {
        "phenotype": str(answers.get("skin_type", answers.get("reaction", "не определён"))),
        "origin": str(answers.get("reaction", "по ответам")),
        "concentration": "основные зоны лица",
        "recommendations": [
            "Использовать SPF защиту",
            "Подобрать уход по типу кожи",
        ],
        "summary": f"Анализ выполнен. Тип: {answers.get('skin_type', '—')}, реакция на солнце: {answers.get('reaction', '—')}.",
        "raw": answers,
    }


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


# --- Analysis flow (per MODELS_AND_FILES.md) ---

@router.post("", response_model=AnalyzeResponse)
def analyze_image(
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    POST /api/analyze
    Body: { image: string } (data URL, e.g. data:image/jpeg;base64,...)
    Returns: { sessionId: string, questions: AnalysisQuestion[] }
    """
    try:
        image_bytes = _parse_data_url(body.image)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    session = AnalysisSession(
        session_id=AnalysisSession.generate_session_id(),
        original_image=image_bytes,
    )
    db.add(session)
    db.commit()

    questions = _get_questions(db)
    return AnalyzeResponse(sessionId=session.session_id, questions=questions)


@router.post("/answers")
def submit_answers(
    body: SubmitAnswersRequest,
    db: Session = Depends(get_db),
):
    """
    POST /api/analyze/answers
    Body: { sessionId: string, answers: Record<string, string | number> }
    Returns: { result: Record<string, unknown> | string }
    """
    session = db.query(AnalysisSession).filter(
        AnalysisSession.session_id == body.sessionId
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = _build_result_from_answers(body.answers)
    session.result = result
    db.commit()

    return {"result": result}


@router.get("/sessions/{session_id}")
def get_session_result(session_id: str, db: Session = Depends(get_db)):
    """
    GET /api/analyze/sessions/{sessionId}
    Returns session with result (for history/display).
    """
    session = db.query(AnalysisSession).filter(
        AnalysisSession.session_id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "sessionId": session.session_id,
        "result": session.result,
    }
