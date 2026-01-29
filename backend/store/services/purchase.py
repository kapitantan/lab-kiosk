from dataclasses import dataclass
from django.db import transaction
from django.db.models import Sum

from store.models import Product, User, StockTransaction
from store.services.notification.discord import send
from django.conf import settings

class PurchaseError(Exception):
    """
    service層の例外。
    API層はこれを捕まえてHTTPのエラーに変換する。
    """
    def __init__(self, error_code: str):
        self.code = error_code
        super().__init__(error_code)

@dataclass(frozen=True)
class PurchaseResult:
    product: Product
    remaining: int

@transaction.atomic
def purchase_one(*, student_id: str, jan_code: str) -> PurchaseResult:
    # 購入者の特定
    try:
        user = User.objects.get(student_id=student_id)
        print(f"{user=}")
    except User.DoesNotExist:
        raise PurchaseError("user_not_found")

    # 商品特定
    try:
        product = Product.objects.select_for_update().get(jan_code=jan_code)
    except Product.DoesNotExist:
        raise PurchaseError("product_not_found")

    # 現在在庫の確認
    current = (
        StockTransaction.objects
        .filter(product=product)
        .aggregate(total=Sum("delta"))
        .get("total")
    ) or 0

    if current <= 0:
        raise PurchaseError("out_of_stock")

    # 購入確定 
    StockTransaction.objects.create(
        product=product,
        user=user,
        delta=-1,
        transaction_type="OUT",
    )

    remaining = current - 1
    threshold = getattr(settings, "LOW_STOCK_THRESHOLD", None)
    if remaining <= threshold:
        message = f"在庫低下: {product.name} (JAN:{product.jan_code}) 残り {remaining}"
        transaction.on_commit(lambda: send(message, username="Lab-Kiosk"))

    return PurchaseResult(product=product, remaining=current - 1)
    # return PurchaseResult(product=Product(), remaing=0)
