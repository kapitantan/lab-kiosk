from django.urls import include, path
from store.api.views import (
    ProductRegisterView,
    PurchaseView,
)

urlpatterns = [
    path("purchases", PurchaseView.as_view(), name="purchases"),
    path("products/register", ProductRegisterView.as_view(), name="product_register"),

]
