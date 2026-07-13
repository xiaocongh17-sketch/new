"""AI assistant API routes."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from app.interfaces.api.deps import require_user, get_ai_model_dep, get_knowledge_repo, get_house_repo
from app.domain.entities.user import User
from app.domain.repositories.knowledge_repository import KnowledgeRepository
from app.domain.repositories.house_repository import HouseRepository
from app.domain.interfaces.ai_model import BaseAIModel
from app.application.dto.house_dto import ChatInput, ChatOutput
from app.application.use_cases.answer_employee_query import AnswerEmployeeQueryUseCase
from app.application.use_cases.collect_house_info import CollectHouseInfoUseCase
from app.interfaces.middleware.rate_limit import get_rate_limiter

router = APIRouter(prefix="/ai", tags=["AI 助手"])
limiter = get_rate_limiter()


@router.post("/chat", response_model=ChatOutput, summary="AI 业务助手对话")
@limiter.limit("10/minute")
async def ai_chat(
    request: Request,
    input: ChatInput,
    current_user: User = Depends(require_user),
    ai_model: BaseAIModel = Depends(get_ai_model_dep),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repo),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Chat with AI business assistant (RAG + House DB)."""
    use_case = AnswerEmployeeQueryUseCase(
        ai_model=ai_model, knowledge_repo=knowledge_repo, house_repo=house_repo,
    )
    try:
        result = await use_case.execute(
            query=input.query,
            store_id=str(current_user.store_id) if current_user.store_id else None,
        )
        return ChatOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


class CollectInput(BaseModel):
    query: str
    history: list[dict] = []
    collected: dict = {}
    mode: str = "collect"
    session_id: str = ""


@router.post("/collect", summary="AI 房源信息采集对话")
@limiter.limit("10/minute")
async def ai_collect(
    request: Request,
    input: CollectInput,
    current_user: User = Depends(require_user),
    ai_model: BaseAIModel = Depends(get_ai_model_dep),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repo),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Multi-turn AI conversation for house info collection."""
    use_case = CollectHouseInfoUseCase(
        ai_model=ai_model, knowledge_repo=knowledge_repo, house_repo=house_repo,
    )
    try:
        result = await use_case.execute(
            query=input.query,
            history=input.history,
            collected=input.collected,
            store_id=str(current_user.store_id) if current_user.store_id else None,
            session_id=input.session_id or str(current_user.id),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI collect error: {str(e)}")
