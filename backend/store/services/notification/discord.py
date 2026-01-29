import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send(content: str, *, username: Optional[str] = None) -> bool:
    """
    Discord Webhook にメッセージを送信する。
    - 失敗しても例外は投げない
    - 成否を bool で返す
    """
    webhook_url = getattr(settings, "DISCORD_WEBHOOK_URL", None)

    # Webhook 未設定時は何もしない（local / test 用）
    if not webhook_url:
        logger.debug("DISCORD_WEBHOOK_URL is not set. Skip discord notification.")
        return True

    payload = _build_payload(content, username)

    try:
        return _post(webhook_url, payload)
    except Exception:
        logger.exception("Failed to send discord notification")
        return False


def _build_payload(content: str, username: Optional[str]) -> dict:
    payload = {
        "content": content,
    }
    if username:
        payload["username"] = username
    return payload


def _post(webhook_url: str, payload: dict) -> bool:
    response = requests.post(
        webhook_url,
        json=payload,
        timeout=5,  # 固定で十分。必要なら後で settings 化
    )

    if 200 <= response.status_code < 300:
        return True
    logger.warning(
        "Discord webhook returned non-2xx status",
        extra={
            "status_code": response.status_code,
            "response_text": response.text,
        },
    )
    return False
