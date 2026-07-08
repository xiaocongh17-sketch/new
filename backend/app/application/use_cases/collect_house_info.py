"""State-machine driven house info collection. AI only handles NL, code owns state."""
import json, re, uuid, asyncio, structlog
from decimal import Decimal
from app.domain.repositories.knowledge_repository import KnowledgeRepository
from app.domain.repositories.house_repository import HouseRepository
from app.domain.interfaces.ai_model import BaseAIModel, ChatMessage

logger = structlog.get_logger()

# Strict step sequence — code enforces order, AI cannot deviate
STEPS = [
    ("community", "小区名称", "这个房子在哪个小区？"),
    ("area", "面积", "房子多大面积？多少平米？"),
    ("room_type", "户型", "几室几厅几卫？"),
    ("rent_price", "价格", "打算卖多少钱？或者租多少钱？"),
    ("building_type", "建筑类型", "高层、小高层、洋房还是超高层？"),
    ("floor_info", "楼层", "总高几层？房子在第几层？"),
    ("decoration", "装修", "装修情况是精装、简装还是毛坯？"),
    ("decoration_year", "装修年份", "哪一年装修的？保养得怎么样？"),
    ("occupancy_status", "居住状态", "业主自住、出租还是空置？"),
    ("listed_on_beike", "贝壳挂牌", "有没有挂到贝壳网上？"),
    ("list_price", "挂牌价", "贝壳上挂的价格是多少？（没挂贝壳就说你们自己的挂牌价）"),
    ("has_parking", "车位", "带不带车位？几个？"),
    ("key_location", "钥匙/看房", "钥匙在哪？怎么看房？密码锁还是钥匙？"),
    ("list_duration", "挂牌时长", "挂了多久了？"),
    ("unsold_reason", "未成交原因", "有人出过价吗？为什么没卖掉？"),
    ("purchase_year", "购置年份", "业主哪一年买的？"),
    ("is_only_home", "唯一住房", "是业主唯一住房吗？"),
    ("seller_motivation", "卖房动机", "业主为什么卖房？"),
]

# Simple regex fallbacks when AI miss-extracts
PATTERNS = {
    "key_location": ["密码锁", "密码", "钥匙在物业", "钥匙在门店", "钥匙在我这", "钥匙在店里"],
    "has_parking": ["有车位", "带车位", "有停车位", "带停车位", "有车库"],
    "no_parking": ["没车位", "不带车位", "没有车位", "无车位"],
    "listed_on_beike": ["挂了贝壳", "贝壳上有", "贝壳挂", "上架贝壳"],
    "not_listed_beike": ["没挂贝壳", "没上贝壳", "不上贝壳", "不挂贝壳", "没上架"],
    "occupancy_self": ["业主自住", "自己住", "自住", "自己住的", "房东住"],
    "occupancy_empty": ["空置", "空着", "没人住", "空关", "毛坯空关", "闲置"],
    "occupancy_rented": ["出租中", "租出去了", "租给", "在出租", "有租客"],
    "decoration_fine": ["精装", "精装修", "豪装"],
    "decoration_simple": ["简装", "简单装修", "普装"],
    "decoration_raw": ["毛坯", "毛坯房", "清水"],
}

EXTRACT_PROMPT = """从用户消息中提取房产信息，只返回JSON。

用户说：{query}

字段：
{fields_help}

只提取用户明确提到的信息。格式：
{{"field_name": "value"}}"""


class CollectHouseInfoUseCase:
    _sessions: dict[str, dict] = {}  # session_id -> {step_index, collected}

    def __init__(self, ai_model, knowledge_repo, house_repo=None):
        self.ai_model = ai_model
        self.knowledge_repo = knowledge_repo
        self.house_repo = house_repo

    async def execute(self, query, history, collected, store_id=None, session_id=""):
        sid = session_id or "default"
        if sid not in self._sessions:
            # Initialize: merge any frontend state
            self._sessions[sid] = {"step": 0, "collected": dict(collected)}
        state = self._sessions[sid]
        # Merge incoming frontend state
        for k, v in collected.items():
            if v is not None and v != "" and v is not False:
                state["collected"][k] = v
        if collected:
            for k, v in collected.items():
                if isinstance(v, bool) and v is False:
                    state["collected"][k] = False

        # ── Step 1: Find current step for context-aware extraction ──
        current_step_key, current_step_label, current_step_hint = STEPS[min(state["step"], len(STEPS)-1)]

        # Extract info from user message — tell extractor which field we're looking for
        fields_help = ", ".join(f"{s[0]}({s[1]})" for s in STEPS)
        ext_prompt = f"""从用户消息中提取房产信息，只返回JSON。
当前我们在采集：{current_step_label}（字段名：{current_step_key}）
用户说：{query}
可用字段：{fields_help}
规则：优先且必须提取「{current_step_label}」的值到 {current_step_key} 字段！其他提到的信息也提取。"""
        ext_messages = [ChatMessage(role="system", content="你是房产信息提取器，只返回JSON。"),
                        ChatMessage(role="user", content=ext_prompt)]

        extracted = {}
        try:
            for attempt in range(3):
                try:
                    ext_resp = await self.ai_model.chat(ext_messages, temperature=0)
                    content = ext_resp.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    if "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    data = json.loads(content.strip())
                    # Only accept known field keys
                    known_keys = {s[0] for s in STEPS}
                    for k, v in data.items():
                        if k in known_keys and v is not None and v != "":
                            extracted[k] = str(v) if not isinstance(v, bool) else v
                    break
                except Exception:
                    if attempt == 2:
                        logger.warning("extraction_failed", query=query[:50])
                    await asyncio.sleep(0.5)
        except Exception:
            pass

        # Regex fallback for duration
        dur = re.search(r'(\d+)\s*[个]?\s*[月天周年]', query)
        if dur and current_step_key == "list_duration":
            extracted["list_duration"] = dur.group(0)

        # Regex fallbacks for common expressions AI might miss
        for pat in PATTERNS.get("key_location", []):
            if pat in query: extracted["key_location"] = pat; break
        if "不带车位" in query or "没车位" in query:
            extracted["has_parking"] = False
        elif "带车位" in query or "有车位" in query:
            extracted["has_parking"] = True
        if "没挂贝壳" in query or "不挂贝壳" in query:
            extracted["listed_on_beike"] = False
        elif "挂了贝壳" in query or "上架贝壳" in query:
            extracted["listed_on_beike"] = True
        for occ_pat in PATTERNS.get("occupancy_self", []):
            if occ_pat in query: extracted["occupancy_status"] = "自住"; break
        for occ_pat in PATTERNS.get("occupancy_empty", []):
            if occ_pat in query: extracted["occupancy_status"] = "空置"; break
        for deco_pat in PATTERNS.get("decoration_fine", []):
            if deco_pat in query: extracted["decoration"] = "精装"; break

        # Auto-fill list_price from rent_price if stuck
        if state["collected"].get("rent_price") and not extracted.get("list_price"):
            if "list_price" not in state["collected"] or not state["collected"]["list_price"]:
                if current_step_key == "list_price":
                    extracted["list_price"] = state["collected"]["rent_price"]

        # Merge extracted into collected
        for k, v in extracted.items():
            if k not in state["collected"] or state["collected"].get(k) is None or state["collected"].get(k) == "":
                state["collected"][k] = v

        # ── Step 2: Find current step ──
        # Advance step past completed fields
        while state["step"] < len(STEPS):
            step_key = STEPS[state["step"]][0]
            val = state["collected"].get(step_key)
            if val is not None and val != "" and val is not False:
                state["step"] += 1
            elif isinstance(val, bool) and val is False:
                state["step"] += 1
            else:
                break

        # ── Step 3: Generate natural reply ──
        if state["step"] >= len(STEPS):
            reply = "所有信息已采集完毕！房源记录已自动保存，可以在房源管理中查看。"
            real_next = ""
            score = 100
        else:
            current = STEPS[state["step"]]
            col_list = ", ".join(f"{k}={v}" for k, v in state["collected"].items()
                                 if v is not None and v != "")

            chat_prompt = f"""你是房产采集助手「小房」。用户刚说：{query}

已采集：{col_list}
本轮提取到的新信息：{json.dumps({k: str(v) for k, v in extracted.items()}, ensure_ascii=False)}

请自然回复：
1. 先确认用户刚才说的内容（如果提取到了新信息就提一下）
2. 然后问下一个问题：{current[2]}
3. 只问这一个问题，不要问其他的
4. 像同事聊天一样自然，不要机械"""

            reply = query  # fallback
            for attempt in range(3):
                try:
                    resp = await self.ai_model.chat(
                        [ChatMessage(role="system", content=chat_prompt)], temperature=0.4
                    )
                    reply = resp.content.strip()
                    break
                except Exception:
                    if attempt == 2:
                        reply = f"好的，收到。{current[2]}"
                    await asyncio.sleep(1)

            real_next = current[0]

            # Move step forward since we just asked about it
            # (will advance on next call when user answers)
            merged = dict(state["collected"])
            score = min(100, sum(1 for v in merged.values() if v is not None and v != "") * 5)

        # ── Step 4: Build merged for response ──
        merged = dict(state["collected"])

        # Auto-save
        house_id = None
        core = ["community", "area", "room_type", "rent_price", "occupancy_status"]
        if all(merged.get(f) for f in core) and self.house_repo:
            try:
                house_id = await self._auto_save(merged, store_id)
            except Exception:
                pass

        return {
            "reply": reply,
            "extracted": {k: (str(v) if not isinstance(v, bool) else v) for k, v in extracted.items()},
            "next_question": real_next if state["step"] < len(STEPS) else "",
            "score": min(100, sum(1 for v in merged.values() if v is not None and v != "") * 5),
            "house_id": str(house_id) if house_id else None,
            "core_complete": all(merged.get(f) for f in core),
        }

    async def _auto_save(self, data, store_id):
        from app.domain.entities.house import House
        price = Decimal(str(data.get("rent_price") or data.get("list_price") or 0))
        area = Decimal(str(data.get("area", 0)))
        house = House.create(
            community=data.get("community", ""), area=area,
            room_type=data.get("room_type", ""), rent_price=price,
            owner_id=uuid.uuid4(),
            store_id=uuid.UUID(store_id) if store_id else None,
            decoration=data.get("decoration"), floor_info=data.get("floor_info"),
            building_type=data.get("building_type"),
            has_parking=data.get("has_parking") in [True, "true", "是", "yes", "有", True],
            occupancy_status=data.get("occupancy_status"),
            decoration_year=data.get("decoration_year"),
            key_location=data.get("key_location"),
            viewing_password=data.get("viewing_password"),
            listed_on_beike=data.get("listed_on_beike") in [True, "true", "是", "yes", "有", True],
            list_price=Decimal(str(data["list_price"])) if data.get("list_price") else None,
            list_duration=data.get("list_duration"),
            unsold_reason=data.get("unsold_reason"),
            purchase_year=data.get("purchase_year"),
            is_only_home=data.get("is_only_home") in [True, "true", "是", "yes", True],
            seller_motivation=data.get("seller_motivation"),
            ai_collected_fields=",".join(k for k, v in data.items() if v is not None and v != ""),
            collector_score=min(100, sum(1 for v in data.values() if v is not None and v != "") * 5),
        )
        saved = await self.house_repo.save(house)
        return saved.id
