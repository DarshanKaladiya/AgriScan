from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('crops/', views.crops_list, name='crops_list'),
    path('crop/<int:crop_id>/', views.crop_detail, name='crop_detail'),
    path('compare/', views.compare_products, name='compare_products'),
    path('mandi/', views.mandi_rates, name='mandi_rates'),
    path('companies/', views.partners_list, name='partners_list'),
]
