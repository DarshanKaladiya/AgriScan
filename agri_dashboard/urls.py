from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('scanner/', views.scanner_view, name='scanner'),
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
    path('set-language/', views.set_language, name='set_language'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'core' / 'static')

