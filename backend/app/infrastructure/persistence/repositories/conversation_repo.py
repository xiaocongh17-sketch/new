"""SQLAlchemy implementation of ConversationRepository."""

import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.repositories.conversation_repository import ConversationRepository
from app.domain.value_objects.enums import ConversationStatus, MessageType
from app.infrastructure.persistence.models.conversation import ConversationModel
from app.infrastructure.persistence.models.message import MessageModel


class SQLAlchemyConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: uuid.UUID) -> Conversation | None:
        result = await self.session.execute(
            select(ConversationModel).where(ConversationModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_active_by_group(self, wecom_group_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(ConversationModel).where(
                ConversationModel.wecom_group_id == wecom_group_id,
                ConversationModel.status == "active",
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_store(self, store_id: uuid.UUID,
                            page: int = 1,
                            page_size: int = 20) -> tuple[list[Conversation], int]:
        query = select(ConversationModel).where(ConversationModel.store_id == store_id)
        count_query = select(func.count()).select_from(ConversationModel).where(
            ConversationModel.store_id == store_id
        )

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(ConversationModel.updated_at.desc()).offset(offset).limit(page_size)
        )
        items = [self._to_domain(m) for m in result.scalars().all()]
        return items, total

    async def save(self, conversation: Conversation) -> Conversation:
        model = self._to_orm(conversation)
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def add_message(self, message: Message) -> Message:
        model = MessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            content=message.content,
            msg_type=message.msg_type.value if message.msg_type else "text",
            wecom_msg_id=message.wecom_msg_id,
        )
        self.session.add(model)
        await self.session.flush()
        return message

    async def get_messages(self, conversation_id: uuid.UUID,
                           limit: int = 50) -> list[Message]:
        result = await self.session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
        )
        return [self._to_message_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: ConversationModel) -> Conversation:
        # Participants stored as JSON array of UUID strings → convert to UUID objects
        raw_participants = model.participants or []
        participants = [uuid.UUID(p) if isinstance(p, str) else p for p in raw_participants]
        return Conversation(
            id=model.id,
            wecom_group_id=model.wecom_group_id,
            participants=participants,
            context=model.context or {},
            status=ConversationStatus(model.status) if model.status else ConversationStatus.ACTIVE,
            store_id=model.store_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_orm(self, domain: Conversation) -> ConversationModel:
        return ConversationModel(
            id=domain.id,
            wecom_group_id=domain.wecom_group_id,
            participants=[str(p) for p in (domain.participants or [])],
            context=domain.context,
            status=domain.status.value if domain.status else "active",
            store_id=domain.store_id,
        )

    def _to_message_domain(self, model: MessageModel) -> Message:
        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            sender_id=model.sender_id,
            content=model.content,
            msg_type=MessageType(model.msg_type) if model.msg_type else MessageType.TEXT,
            wecom_msg_id=model.wecom_msg_id,
            created_at=model.created_at,
        )
