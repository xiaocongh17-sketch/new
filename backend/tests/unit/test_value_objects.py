"""Unit tests for domain value objects and enumerations.

Tests cover:
    - UserRole enum values and methods
    - DecorationType enum values
    - HouseStatus enum values and lifecycle
    - ConversationStatus enum values
    - MessageType enum values
    - HouseSource enum values
"""

import pytest
from app.domain.value_objects.enums import (
    UserRole,
    DecorationType,
    HouseStatus,
    ConversationStatus,
    MessageType,
    HouseSource,
)


# ===================================================================
# UserRole
# ===================================================================
class TestUserRole:
    def test_enum_values(self):
        """Should have the expected string values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.STORE_MANAGER.value == "store_manager"
        assert UserRole.AGENT.value == "agent"
        assert UserRole.LANDLORD.value == "landlord"

    def test_enum_members_count(self):
        """Should have exactly four roles."""
        assert len(UserRole) == 4

    def test_str_inheritance(self):
        """Should be a string enum (inherit from str)."""
        assert isinstance(UserRole.ADMIN, str)
        # str() on an Enum member returns the member name (Enum.__str__),
        # .value returns the underlying string value.
        assert UserRole.ADMIN.value == "admin"

    def test_from_value_valid(self):
        """Should parse from string value."""
        assert UserRole("admin") == UserRole.ADMIN
        assert UserRole("store_manager") == UserRole.STORE_MANAGER
        assert UserRole("agent") == UserRole.AGENT
        assert UserRole("landlord") == UserRole.LANDLORD

    def test_from_value_invalid_raises(self):
        """Should raise ValueError for invalid role value."""
        with pytest.raises(ValueError):
            UserRole("super_admin")

    def test_comparison(self):
        """Should support equality comparison between members."""
        assert UserRole.ADMIN == UserRole.ADMIN
        assert UserRole.ADMIN != UserRole.AGENT

    def test_in_set(self):
        """Should be usable in set membership checks."""
        allowed = {UserRole.ADMIN, UserRole.STORE_MANAGER}
        assert UserRole.ADMIN in allowed
        assert UserRole.AGENT not in allowed


# ===================================================================
# DecorationType
# ===================================================================
class TestDecorationType:
    def test_enum_values(self):
        """Should have the expected string values."""
        assert DecorationType.ROUGH.value == "rough"
        assert DecorationType.SIMPLE.value == "simple"
        assert DecorationType.HARDCOVER.value == "hardcover"
        assert DecorationType.LUXURY.value == "luxury"

    def test_enum_members_count(self):
        """Should have exactly four decoration types."""
        assert len(DecorationType) == 4

    def test_str_inheritance(self):
        """Should be a string enum."""
        assert isinstance(DecorationType.HARDCOVER, str)
        assert DecorationType.HARDCOVER.value == "hardcover"


# ===================================================================
# HouseStatus
# ===================================================================
class TestHouseStatus:
    def test_enum_values(self):
        """Should have the expected string values."""
        assert HouseStatus.PENDING.value == "pending"
        assert HouseStatus.ACTIVE.value == "active"
        assert HouseStatus.RENTED.value == "rented"
        assert HouseStatus.OFF.value == "off"

    def test_enum_members_count(self):
        """Should have exactly four statuses."""
        assert len(HouseStatus) == 4

    def test_lifecycle_order(self):
        """Should reflect typical lifecycle constants."""
        # A house starts as PENDING or ACTIVE
        assert HouseStatus.PENDING is not None
        assert HouseStatus.ACTIVE is not None
        # It can end up RENTED or OFF
        assert HouseStatus.RENTED is not None
        assert HouseStatus.OFF is not None

    def test_str_inheritance(self):
        """Should be a string enum."""
        assert isinstance(HouseStatus.ACTIVE, str)
        assert HouseStatus.ACTIVE.value == "active"

    def test_from_value(self):
        """Should parse from string value."""
        assert HouseStatus("active") == HouseStatus.ACTIVE
        assert HouseStatus("rented") == HouseStatus.RENTED


# ===================================================================
# ConversationStatus
# ===================================================================
class TestConversationStatus:
    def test_enum_values(self):
        """Should have the expected string values."""
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PENDING_REVIEW.value == "pending_review"
        assert ConversationStatus.CLOSED.value == "closed"

    def test_enum_members_count(self):
        """Should have exactly three statuses."""
        assert len(ConversationStatus) == 3

    def test_str_inheritance(self):
        """Should be a string enum."""
        assert isinstance(ConversationStatus.ACTIVE, str)
        assert ConversationStatus.ACTIVE.value == "active"


# ===================================================================
# MessageType
# ===================================================================
class TestMessageType:
    def test_enum_values(self):
        """Should have the expected string values."""
        assert MessageType.TEXT.value == "text"
        assert MessageType.IMAGE.value == "image"
        assert MessageType.SYSTEM.value == "system"

    def test_enum_members_count(self):
        """Should have exactly three types."""
        assert len(MessageType) == 3

    def test_str_inheritance(self):
        """Should be a string enum."""
        assert isinstance(MessageType.TEXT, str)
        assert MessageType.TEXT.value == "text"


# ===================================================================
# HouseSource
# ===================================================================
class TestHouseSource:
    def test_enum_values(self):
        """Should have the expected string values."""
        assert HouseSource.WECHAT.value == "wechat"
        assert HouseSource.MANUAL.value == "manual"
        assert HouseSource.IMPORT.value == "import"

    def test_enum_members_count(self):
        """Should have exactly three sources."""
        assert len(HouseSource) == 3

    def test_str_inheritance(self):
        """Should be a string enum."""
        assert isinstance(HouseSource.MANUAL, str)
        assert HouseSource.MANUAL.value == "manual"
