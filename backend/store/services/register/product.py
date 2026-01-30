# store/services/register/product.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from store.models import Product

logger = logging.getLogger(__name__)


@transaction.atomic
def register_product(*, validated_data: Dict[str, Any]) -> Product:
    """
    商品を新規登録する。

    validated_data は Serializer.is_valid() 済みを想定。
    ただし同時実行などで unique 制約に引っかかる可能性があるため、
    IntegrityError はここで ValidationError に変換して返す。
    """
    try:
        product = Product.objects.create(**validated_data)
        return product

    except IntegrityError as e:
        # 例: jan_code の unique 制約競合（同時登録など）
        logger.warning(
            "Failed to register product due to integrity error",
            extra={"validated_data": _safe_log_payload(validated_data)},
            exc_info=True,
        )
        raise ValidationError({"jan_code": "このJANコードの商品は既に登録されています。"}) from e


def _safe_log_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ログに出してよい最低限の情報に絞る（将来、機微情報が増えても安全）
    """
    return {
        "jan_code": data.get("jan_code"),
        "name": data.get("name"),
        "price": data.get("price"),
        "alert_threshold": data.get("alert_threshold"),
        "image_url": data.get("image_url"),
    }
