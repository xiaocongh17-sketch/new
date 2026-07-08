"""WeCom message encryption/decryption.

Uses BaseWeChatCrypto directly because wechatpy's WeChatCrypto
is designed for 公众号 (uses app_id), while WeCom (企业微信)
requires passing corp_id as the _id parameter.
"""

from __future__ import annotations

from wechatpy.crypto import BaseWeChatCrypto, PrpCrypto
from wechatpy.exceptions import InvalidSignatureException
from app.infrastructure.config.settings import settings

_crypto: "WeComCrypto" | None = None


class WeComCrypto(BaseWeChatCrypto):
    """WeCom-compatible crypto wrapper around BaseWeChatCrypto.

    Exposes check_signature, decrypt_message, and encrypt_message
    as public methods (they are private on BaseWeChatCrypto).
    """

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str) -> None:
        super().__init__(token, encoding_aes_key, corp_id)

    def check_signature(self, signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """Verify signature and decrypt echostr. Returns the plaintext."""
        return self._check_signature(signature, timestamp, nonce, echostr, PrpCrypto)

    def decrypt_message(self, msg: str, signature: str, timestamp: str, nonce: str) -> str:
        """Decrypt an encrypted message XML."""
        return self._decrypt_message(msg, signature, timestamp, nonce, PrpCrypto)

    def encrypt_message(self, msg: str, nonce: str, timestamp: str | None = None) -> str:
        """Encrypt a reply message XML."""
        return self._encrypt_message(msg, nonce, timestamp, PrpCrypto)


def get_crypto() -> WeComCrypto:
    """Get or create the WeComCrypto singleton."""
    global _crypto
    if _crypto is None:
        _crypto = WeComCrypto(
            token=settings.wecom_token,
            encoding_aes_key=settings.wecom_encoding_aes_key,
            corp_id=settings.wecom_corp_id,
        )
    return _crypto


def verify_url(signature: str, timestamp: str, nonce: str, echostr: str) -> str:
    """Verify URL challenge from WeCom. Returns decrypted echostr."""
    crypto = get_crypto()
    try:
        return crypto.check_signature(signature, timestamp, nonce, echostr)
    except InvalidSignatureException:
        raise ValueError("Invalid WeCom signature")


def decrypt_message(signature: str, timestamp: str, nonce: str, xml_data: str) -> str:
    """Decrypt an encrypted WeCom message XML."""
    crypto = get_crypto()
    return crypto.decrypt_message(xml_data, signature, timestamp, nonce)


def encrypt_message(reply_xml: str, nonce: str, timestamp: str | None = None) -> str:
    """Encrypt a reply message for WeCom."""
    from datetime import datetime

    crypto = get_crypto()
    timestamp = timestamp or str(int(datetime.now().timestamp()))
    return crypto.encrypt_message(reply_xml, nonce, timestamp)
