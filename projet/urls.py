from django.contrib import admin
from django.urls import path, include, re_path
from DHT import views
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('DHT.urls')),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('index/', views.table, name='table'),
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),

]
