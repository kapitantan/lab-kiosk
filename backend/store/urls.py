from django.urls import path,include
from store.api.views import PurchaseView

urlpatterns = [
    path('purchases',PurchaseView.as_view(),name='purchases'),
    
]
