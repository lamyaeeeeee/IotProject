from django.contrib import admin
from django.urls import path, include
from DHT import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('DHT.urls')),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('index/', views.table, name='table'),

]
