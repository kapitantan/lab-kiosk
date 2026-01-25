from django.urls import path,include
from store.api.views import PurchaseView

urlpatterns = [
    path('purcases',PurchaseView.as_view(),name='purchase'),
    
]
