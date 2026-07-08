"""Unit tests for domain value objects."""

from app.domain.value_objects.enums import (
    UserRole, DecorationType, HouseStatus,
    ConversationStatus, MessageType, HouseSource,
)


class TestUserRole:
    def test_values(self):
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.STORE_MANAGER.value == "store_manager"
        assert UserRole.AGENT.value == "agent"
        assert UserRole.LANDLORD.value == "landlord"


class TestDecorationType:
    def test_values(self):
        assert DecorationType.ROUGH.value == "rough"
        assert DecorationType.SIMPLE.value == "simple"
        assert DecorationType.HARDCOVER.value == "hardcover"
        assert DecorationType.LUXURY.value == "luxury"


class TestHouseStatus:
    def test_values(self):
        assert HouseStatus.PENDING.value == "pending"
        assert HouseStatus.ACTIVE.value == "active"
        assert HouseStatus.RENTED.value == "rented"
        assert HouseStatus.OFF.value == "off"


class TestConversationStatus:
    def test_values(self):
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PENDING_REVIEW.value == "pending_review"
        assert ConversationStatus.CLOSED.value == "closed"


class TestMessageType:
    def test_values(self):
        assert MessageType.TEXT.value == "text"
        assert MessageType.IMAGE.value == "image"
        assert MessageType.SYSTEM.value == "system"
