from django.urls import include, path
from rest_framework.routers import DefaultRouter

from store.api.views import (
    ProductRegisterView,
    PurchaseView,
    StockTransactionViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r"transactions", StockTransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("purchases", PurchaseView.as_view(), name="purchases"),
    path("products/register", ProductRegisterView.as_view(), name="product_register"),

]
