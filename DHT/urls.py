from django.urls import path
from . import views
from . import api
from django.contrib.auth import views as auth_views
from .api import enregistrement_list
from .api_operateurs import operateur_list, operateur_detail
urlpatterns = [
    path("api",api.Dlist,name='json'),
    path("api/post",api.Dlist,name='json'),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('index/',views.table,name='table'),
    path('myChartTemp/',views.graphiqueTemp,name='myChartTemp'),
    path('myChartHum/', views.graphiqueHum, name='myChartHum'),
    path('chart-data/', views.chart_data, name='chart-data'),

    path('chart-data-jour/',views.chart_data_jour,name='chart-data-jour'),
    path('chart-data-semaine/',views.chart_data_semaine,name='chart-data-semaine'),
    path('chart-data-mois/',views.chart_data_mois,name='chart-data-mois'),
    path('', views.home, name='home'),
    path('api/enregistrements/', enregistrement_list, name='enregistrement-list'),
    path('api/temperature-thresholds/', api.temperature_thresholds, name='temperature-thresholds'),
    path('api/operators/', api.get_operators, name='get_operators'),
    path('api/operator-assignments/', api.operator_assignments, name='operator_assignments'),
    path('api/sensor-data/', api.get_sensor_with_latest_data, name='sensor-data'),
    path('api/operateurs/', operateur_list, name='operateur-list'),
    path('api/operateurs/<int:pk>/', operateur_detail, name='operateur-detail'),
]