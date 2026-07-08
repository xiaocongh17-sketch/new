"""Debug collect use case."""
import asyncio, sys, traceback

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.application.use_cases.collect_house_info import CollectHouseInfoUseCase
from app.infrastructure.persistence.database import async_session_factory
from app.infrastructure.persistence.repositories.knowledge_repo import SQLAlchemyKnowledgeRepository
from app.infrastructure.persistence.repositories.house_repo import SQLAlchemyHouseRepository
from app.infrastructure.ai.factory import get_ai_model


async def test():
    model = get_ai_model()
    async with async_session_factory() as session:
        knowledge_repo = SQLAlchemyKnowledgeRepository(session)
        house_repo = SQLAlchemyHouseRepository(session)
        use_case = CollectHouseInfoUseCase(
            ai_model=model, knowledge_repo=knowledge_repo, house_repo=house_repo,
        )

        try:
            result = await use_case.execute(
                query="hello",
                history=[],
                collected={},
                store_id=None,
            )
            print(f"Reply len: {len(result['reply'])}")
            print(f"Extracted: {result['extracted']}")
            print(f"Score: {result['score']}")
            print(f"House saved: {result['house_id']}")
            print(f"Core complete: {result['core_complete']}")
            print("SUCCESS")
        except Exception as e:
            traceback.print_exc()

    await model.client.close()

asyncio.run(test())
