from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """POST /api/analyze - image as data URL (e.g. data:image/jpeg;base64,...)."""
    image: str


class AnalysisQuestionSchema(BaseModel):
    id: str
    label: str
    type: str  # "text" | "select" | "number"
    options: list[str] | None = None


class AnalyzeResponse(BaseModel):
    sessionId: str
    questions: list[AnalysisQuestionSchema]


class SubmitAnswersRequest(BaseModel):
    """POST /api/analyze/answers."""
    sessionId: str
    answers: dict[str, str | int | float]

