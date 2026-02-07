from django.urls import include, path
from rest_framework.routers import DefaultRouter

from store.api.views import (
    csrf,
    ProductRegisterView,
    PurchaseView,
    RestockImportView,
    StockTransactionViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register(r"transactions", StockTransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("csrf", csrf, name="csrf"),
    path("purchases", PurchaseView.as_view(), name="purchases"),
    path("products/register", ProductRegisterView.as_view(), name="product_register"),
    path("restocks/import", RestockImportView.as_view(), name="restock_import"),

]
