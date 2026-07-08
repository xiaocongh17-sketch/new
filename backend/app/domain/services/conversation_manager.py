"""Domain service: manage conversation context and escalation logic."""

ESCALATION_KEYWORDS = [
    "投诉", "法律", "律师", "起诉", "法院", "举报",
    "赔偿", "违法", "欺诈",
]

SPECIAL_REQUIREMENT_KEYWORDS = [
    "特殊", "例外", "帮忙", "急", "马上", "立即",
]


class ConversationManager:
    """Domain service for conversation state management."""

    def should_escalate(self, content: str) -> tuple[bool, str]:
        """Check if a message requires human escalation.

        Returns:
            Tuple of (should_escalate, reason)
        """
        for keyword in ESCALATION_KEYWORDS:
            if keyword in content:
                return True, f"检测到关键词: {keyword}，需要人工处理"
        return False, ""

    def get_next_prompt(self, missing_fields: list[str]) -> str | None:
        """Get the next question to ask based on missing fields."""
        if not missing_fields:
            return None

        from .house_extraction_service import FIELD_PROMPTS
        return FIELD_PROMPTS.get(missing_fields[0])
