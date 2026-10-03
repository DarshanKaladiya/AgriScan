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
    
    # AgriScan Authentication & Personal Scans
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('my-scans/', views.my_scans, name='my_scans'),
    path('field-reports/', views.field_reports, name='field_reports'),
]
