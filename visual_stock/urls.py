from django.contrib import admin
from django.urls import path, include
from stock_price import views




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('visual_stock/', include('stock_price.urls')),
]
