from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import require_any_dashboard
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/chatbot", tags=["Assistant conversationnel"])

@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    llm = LLMService()

    region_context = (
        f"Filtre OBLIGATOIRE sur la région '{current_user.region_assignee}'."
        if current_user.region_assignee
        else "Accès à toutes les régions."
    )

    try:
        return await llm.text_to_sql_and_answer(
            question=payload.message,
            history=payload.history,
            region_context=region_context,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))