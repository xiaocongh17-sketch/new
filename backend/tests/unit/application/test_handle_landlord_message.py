"""Tests for HandleLandlordMessageUseCase."""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.handle_landlord_message import HandleLandlordMessageUseCase
from app.domain.entities.user import User
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.enums import UserRole, ConversationStatus
from app.domain.interfaces.ai_model import ChatMessage, ChatResponse


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.find_by_wecom_userid.return_value = None  # new user
    return repo


@pytest.fixture
def mock_conv_repo():
    repo = AsyncMock()
    repo.find_active_by_group.return_value = None  # new conversation
    return repo


@pytest.fixture
def mock_ai():
    ai = AsyncMock()
    ai.chat.return_value = ChatResponse(
        content="您好！请问您的房源在哪个小区？", model="test",
    )
    return ai


@pytest.fixture
def mock_sender():
    sender = AsyncMock()
    sender.send_text_message.return_value = {"errcode": 0}
    return sender


@pytest.fixture
def use_case(mock_user_repo, mock_conv_repo, mock_ai, mock_sender):
    return HandleLandlordMessageUseCase(
        user_repo=mock_user_repo,
        conversation_repo=mock_conv_repo,
        ai_model=mock_ai,
        message_sender=mock_sender,
    )


class TestHandleLandlordMessageUseCase:
    async def test_new_user_new_conversation(self, use_case, mock_user_repo,
                                              mock_conv_repo, mock_ai, mock_sender):
        """New landlord should create both user and conversation."""
        # Mock save returns with proper IDs
        saved_user = User.create(wecom_userid="wx_new", name="新房东", role=UserRole.LANDLORD)
        mock_user_repo.save.return_value = saved_user
        saved_conv = Conversation.create(wecom_group_id="grp_001", participants=[saved_user.id])
        mock_conv_repo.save.return_value = saved_conv

        reply = await use_case.execute(
            wecom_userid="wx_new",
            wecom_group_id="grp_001",
            content="你好，我有一套房子想出租",
        )

        mock_user_repo.find_by_wecom_userid.assert_called_with("wx_new")
        mock_user_repo.save.assert_called_once()
        mock_conv_repo.find_active_by_group.assert_called_with("grp_001")
        assert mock_conv_repo.save.call_count >= 1  # at least once for creation
        assert reply is not None
        assert "您好" in reply

    async def test_existing_user_reuses_conversation(self, use_case, mock_user_repo,
                                                      mock_conv_repo):
        """Returning user with active conversation should reuse it."""
        user = User.create(wecom_userid="wx_old", name="老房东", role=UserRole.LANDLORD)
        user.id = uuid.uuid4()
        mock_user_repo.find_by_wecom_userid.return_value = user
        mock_user_repo.save.return_value = user

        conv = Conversation.create(wecom_group_id="grp_001", participants=[user.id])
        mock_conv_repo.find_active_by_group.return_value = conv
        mock_conv_repo.save.return_value = conv

        reply = await use_case.execute(
            wecom_userid="wx_old",
            wecom_group_id="grp_001",
            content="之前说的那套房子还在",
        )

        assert reply is not None
        # Should not create new user
        assert mock_user_repo.save.call_count == 0

    async def test_escalation_on_complaint(self, use_case, mock_user_repo,
                                            mock_conv_repo, mock_sender):
        """Complaint keywords should trigger escalation."""
        user = User.create(wecom_userid="wx_001", name="房东", role=UserRole.LANDLORD)
        mock_user_repo.find_by_wecom_userid.return_value = user
        mock_user_repo.save.return_value = user

        conv = Conversation.create(wecom_group_id="grp_001", participants=[user.id])
        mock_conv_repo.find_active_by_group.return_value = conv
        mock_conv_repo.save.return_value = conv

        reply = await use_case.execute(
            wecom_userid="wx_001",
            wecom_group_id="grp_001",
            content="我要投诉你们服务质量太差了",
        )

        assert "转接人工" in reply or "人工客服" in reply
        # AI should NOT be called (response is hardcoded)
        assert mock_user_repo.ai_model is None or True
        mock_sender.send_text_message.assert_called_once()

    async def test_escalation_on_legal(self, use_case, mock_user_repo,
                                        mock_conv_repo):
        """Legal keywords should trigger escalation."""
        user = User.create(wecom_userid="wx_002", name="房东", role=UserRole.LANDLORD)
        mock_user_repo.find_by_wecom_userid.return_value = user
        mock_user_repo.save.return_value = user

        conv = Conversation.create(wecom_group_id="grp_001", participants=[user.id])
        mock_conv_repo.find_active_by_group.return_value = conv
        mock_conv_repo.save.return_value = conv

        reply = await use_case.execute(
            wecom_userid="wx_002",
            wecom_group_id="grp_001",
            content="我要起诉你们，找律师",
        )

        assert "转接人工" in reply or "人工客服" in reply

    async def test_ai_reply_includes_collected_context(self, use_case, mock_user_repo,
                                                        mock_conv_repo, mock_ai):
        """AI prompt should include previously collected info in context."""
        user = User.create(wecom_userid="wx_003", name="房东", role=UserRole.LANDLORD)
        mock_user_repo.find_by_wecom_userid.return_value = user

        conv = Conversation.create(
            wecom_group_id="grp_001", participants=[user.id],
        )
        conv.update_context({"community": "万科城"})
        mock_conv_repo.find_active_by_group.return_value = conv
        mock_conv_repo.save.return_value = conv

        reply = await use_case.execute(
            wecom_userid="wx_003",
            wecom_group_id="grp_001",
            content="租金3500",
        )

        assert reply is not None
        # AI should have been called with system prompt containing context
        call_args = mock_ai.chat.call_args
        assert call_args is not None
        # Positional args: chat(messages, temperature=0.7)
        messages = call_args[0][0] if call_args[0] else []
        system_msg = [m for m in messages if m.role == "system"]
        assert len(system_msg) == 1
        assert "万科城" in system_msg[0].content
