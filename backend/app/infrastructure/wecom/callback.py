"""WeCom callback message handler — parses XML messages into domain objects."""

import re
import xml.etree.ElementTree as ET
from app.domain.interfaces.messaging import WeComMessage


def parse_message_xml(xml_str: str, bot_name: str | None = None) -> WeComMessage:
    """Parse WeCom message XML into WeComMessage dataclass.

    Supports both private chat and group chat messages.
    For group chat, automatically strips the @bot_name prefix from content.
    """
    root = ET.fromstring(xml_str)

    msg_type = root.findtext("MsgType", "text")
    content = root.findtext("Content", "")

    # Detect group chat via ChatId field
    chat_id = root.findtext("ChatId", None)

    # In group chat, content starts with "@<bot_name>", strip it
    if chat_id and content.startswith("@"):
        stripped = content
        if bot_name:
            prefix = re.escape(f"@{bot_name}")
            stripped = re.sub(rf"^{prefix}\s*", "", content)
        else:
            # Generic: strip leading @word
            stripped = re.sub(r"^@\S+\s*", "", content)
        content = stripped or content  # don't empty out completely

    return WeComMessage(
        msg_id=root.findtext("MsgId", ""),
        from_user=root.findtext("FromUserName", ""),
        to_user=root.findtext("ToUserName", ""),
        content=content,
        msg_type=msg_type,
        create_time=int(root.findtext("CreateTime", "0")),
        agent_id=root.findtext("AgentID", None),
        chat_id=chat_id,
    )
