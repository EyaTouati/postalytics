"""
Route chatbot — Phase 4 (assistant conversationnel Texte-vers-SQL).

Architecture :
  1. L'utilisateur pose une question en langage naturel
  2. Le backend envoie la question + le schéma SQL au LLM
  3. Le LLM génère une requête SQL
  4. Le backend exécute la requête sur le DW PostgreSQL
  5. Le résultat est reformulé en langage naturel par le LLM

État actuel : stub fonctionnel avec réponse mock.
Pour activer le vrai LLM : implémenter _call_llm() dans app/services/llm_service.py
et décommenter l'appel ci-dessous.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
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

    # Contexte de périmètre pour les agents régionaux
    region_context = (
        f"L'utilisateur est un agent régional. Filtre OBLIGATOIRE sur la région '{current_user.region_assignee}'."
        if current_user.region_assignee
        else "L'utilisateur a accès à toutes les régions."
    )

    try:
        result = await llm.text_to_sql_and_answer(
            question=payload.message,
            history=payload.history,
            region_context=region_context,
            db=db,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur LLM : {str(e)}")
