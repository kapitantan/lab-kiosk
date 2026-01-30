from django.urls import path,include
from store.api.views import PurchaseView, ProductRegisterView

urlpatterns = [
    path('purchases',PurchaseView.as_view(),name='purchases'),
    path('products/register',ProductRegisterView.as_view(),name='product_register'),
    
]
