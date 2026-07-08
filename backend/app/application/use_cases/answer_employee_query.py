"""Use case: Answer employee business questions using RAG + House DB."""

import re
import uuid
import structlog
from decimal import Decimal
from app.domain.repositories.knowledge_repository import KnowledgeRepository
from app.domain.repositories.house_repository import HouseRepository
from app.domain.interfaces.ai_model import BaseAIModel, ChatMessage
from app.domain.interfaces.rag import Embedder

logger = structlog.get_logger()

SYSTEM_PROMPT = """你叫「小房」，是一个专业的房地产AI助手，服务于房产经纪人和门店业务员。

## 你的能力
1. **房源查询**：你可以查询门店当前在租/在售的房源数据库，回答关于房源的具体问题
2. **业务知识**：你精通房地产法律、税费、交易流程、营销获客、谈判技巧等专业知识
3. **数据驱动**：你会基于实际房源数据和知识库资料来回答，不会凭空编造

## 回答规则
- 用口语化的方式交流，像和同事聊天一样自然
- 涉及具体房源时，列出小区名、户型、面积、价格、装修、地址等关键信息
- 如果知识库和房源库都没有相关信息，诚实地告诉用户你目前无法回答，并建议咨询店长或专业人士
- 回答简洁实用，重点突出，适合忙碌的业务员快速阅读
- 如果用户问的是法律或税务问题，可以给出参考信息但提醒以最新政策为准

## 参考资料
【知识库】
{context}

【当前房源】
{house_context}"""


class AnswerEmployeeQueryUseCase:
    """Answer employee business questions using RAG + House DB."""

    def __init__(
        self,
        ai_model: BaseAIModel,
        knowledge_repo: KnowledgeRepository,
        house_repo: HouseRepository | None = None,
        embedder: Embedder | None = None,
        retriever: "Retriever | None" = None,
    ):
        self.ai_model = ai_model
        self.knowledge_repo = knowledge_repo
        self.house_repo = house_repo
        from app.infrastructure.rag.embedding import EmbeddingService
        self.embedder = embedder or EmbeddingService()
        from app.infrastructure.rag.retriever import Retriever
        self.retriever = retriever or Retriever(knowledge_repo)

    def _parse_house_filters(self, query: str) -> dict:
        """Extract house search filters from natural language query."""
        filters = {}

        # Area: "100平", "120平米", "80-100平", "100平方"
        area_match = re.search(r'(\d+)\s*平([米方]|公尺)?', query)
        if area_match:
            area = int(area_match.group(1))
            if area < 20:  # likely not area
                area = None
            else:
                # fuzzy range: ±20%
                filters["area_min"] = area * 0.7
                filters["area_max"] = area * 1.3

        # Price: "3000以内", "5000以下", "2000-3000", "2000到3000"
        price_range = re.search(r'(\d+)\s*[-到至]\s*(\d+)\s*[万百千元块]?', query)
        if price_range:
            filters["price_min"] = int(price_range.group(1))
            filters["price_max"] = int(price_range.group(2))
        else:
            price_max = re.search(r'(\d+)\s*[以之]?[内下](的)?', query)
            if price_max:
                filters["price_max"] = int(price_max.group(1))
            price_min = re.search(r'(\d+)\s*[以之]?[上外](的)?', query)
            if price_min:
                filters["price_min"] = int(price_min.group(1))

        # Room type
        for pat, val in [("一室|1室|一房|单间|开间", "一室"), ("两室|2室|二室|两房", "两室"),
                          ("三室|3室|三房", "三室"), ("四室|4室|四房", "四室")]:
            if re.search(pat, query):
                filters["room_type"] = val
                break

        # Community name: "XX小区的" "XX花园" etc
        comm_match = re.search(r'([一-龥]{2,6}(?:花园|苑|城|湾|庭|院|园|府|邸|里|居|舍|小区|社区))', query)
        if comm_match:
            filters["community"] = comm_match.group(1)

        # Decoration
        if "精装" in query: filters["decoration"] = "精装"
        elif "简装" in query: filters["decoration"] = "简装"
        elif "毛坯" in query: filters["decoration"] = "毛坯"

        return filters

    async def _search_houses(self, query: str, store_uuid: uuid.UUID | None) -> str:
        """Smart house search with query-aware filtering."""
        if not self.house_repo:
            return "暂无房源数据。"

        try:
            from app.domain.repositories.house_repository import HouseFilter
            filters = self._parse_house_filters(query)

            result = await self.house_repo.find_by_store(
                store_id=store_uuid,
                filter=HouseFilter(status="active"),
                page=1, page_size=50,
            )
            all_houses = result.items

            if not all_houses:
                return "当前门店暂无在租房源。"

            # Filter by parsed criteria
            matched = []
            for h in all_houses:
                score = 0
                f_area = h.area if isinstance(h.area, Decimal) else Decimal(str(h.area))
                area_val = float(f_area)

                if "area_min" in filters and area_val >= filters["area_min"]:
                    score += 3
                if "area_max" in filters and area_val <= filters["area_max"]:
                    score += 3
                if "room_type" in filters and filters["room_type"] in (h.room_type or ""):
                    score += 5
                if "price_min" in filters:
                    price = float(h.rent_price)
                    if price >= filters["price_min"]: score += 2
                if "price_max" in filters:
                    price = float(h.rent_price)
                    if price <= filters["price_max"]: score += 2
                if "community" in filters and filters["community"] in (h.community or ""):
                    score += 10
                if "decoration" in filters and filters["decoration"] in (h.decoration or ""):
                    score += 5

                if score > 0 or not filters:
                    matched.append((score, h))

            # Sort by relevance score, then show top matches
            matched.sort(key=lambda x: x[0], reverse=True)
            top = matched[:8] if matched else all_houses[:5]
            houses = [h for _, h in top]

            if not houses:
                return "当前门店暂无匹配的房源。"

            lines = []
            for h in houses:
                addr = f"，{h.address}" if h.address else ""
                deco = f"，{h.decoration}" if h.decoration else ""
                floor = f"，{h.floor_info}层" if h.floor_info else ""
                building = f"（{h.building_type}）" if h.building_type else ""
                occ = f"，{h.occupancy_status}" if h.occupancy_status else ""
                lines.append(
                    f"【{h.community}】{h.room_type} | {h.area}平米{building} | "
                    f"月租{h.rent_price}元 | {floor}{deco}{addr}{occ}"
                )
            return "\n".join(lines)
        except Exception as e:
            logger.warning("house_search_failed", error=str(e))
            return "房源查询暂时不可用。"

    async def execute(self, query: str, store_id: str | None = None) -> dict:
        store_uuid = uuid.UUID(store_id) if store_id else None

        # 1. Search knowledge base
        context_items = []
        sources = []
        try:
            try:
                query_embedding = await self.embedder.embed_text(query)
                search_results = await self.retriever.retrieve(
                    query=query, query_embedding=query_embedding,
                    store_id=store_uuid, top_k=5,
                )
            except Exception:
                search_results = await self.retriever.retrieve_keyword_only(
                    query=query, store_id=store_uuid, top_k=5,
                )

            for result in search_results:
                doc = result.document
                context_items.append(f"【{doc.category}】{doc.title}\n{doc.content[:800]}")
                sources.append({
                    "title": doc.title, "category": doc.category,
                    "similarity": getattr(result, 'similarity', 0),
                })
        except Exception as e:
            logger.warning("retrieval_failed", error=str(e))

        # 2. Smart house search
        house_context = await self._search_houses(query, store_uuid)
        if house_context and "暂无" not in house_context and "不可用" not in house_context:
            sources.append({"title": "房源数据库", "category": "HOUSES", "similarity": 1.0})

        context = "\n\n".join(context_items) if context_items else "暂无匹配的知识库资料。"

        # 3. Call AI with improved prompt
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT.format(
                context=context, house_context=house_context,
            )),
            ChatMessage(role="user", content=query),
        ]
        # Higher temperature for more natural conversation
        for attempt in range(3):
            try:
                response = await self.ai_model.chat(messages, temperature=0.7)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning("ai_retry", attempt=attempt + 1, error=str(e))
                import asyncio
                await asyncio.sleep(1)

        return {"answer": response.content, "sources": sources}
