"""Domain enumerations and value objects."""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    STORE_MANAGER = "store_manager"
    AGENT = "agent"
    LANDLORD = "landlord"


class DecorationType(str, Enum):
    ROUGH = "rough"          # 毛坯
    SIMPLE = "simple"        # 简装
    HARDCOVER = "hardcover"  # 精装
    LUXURY = "luxury"        # 豪装


class HouseStatus(str, Enum):
    PENDING = "pending"      # 待审核
    ACTIVE = "active"        # 出租中
    RENTED = "rented"        # 已出租
    OFF = "off"              # 已下架


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"


class HouseSource(str, Enum):
    WECHAT = "wechat"
    MANUAL = "manual"
    IMPORT = "import"
