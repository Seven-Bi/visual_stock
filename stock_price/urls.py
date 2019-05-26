from django.urls import path
from stock_price import views




urlpatterns = [
    path('save_profits', views.save_profits),
    path('get_latest_data', views.get_latest_data),
    path('get_max_profits', views.get_max_profits),
]