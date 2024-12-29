from django.urls import path
from . import views
from . import api
from django.contrib.auth import views as auth_views
from .api import enregistrement_list
from .api_operateurs import operateur_list, operateur_detail
from .api_login import api_login, get_user_role
from .incident_views import get_active_incidents, acquit_incident
from .api_logout import  api_logout
from .api_sensors import get_sensors_data, get_sensor_details
from .api_sensors import add_sensor, edit_sensor,delete_sensor
from .api_incident_history import get_incidents_history
from .api_incident_history import get_incident_details
from .api_enregistrement import get_capteurs_list, add_enregistrement
from .api import get_sensor_with_latest_data

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

    path('api/operateurs/', operateur_list, name='operateur-list'),
    path('api/operateurs/<int:pk>/', operateur_detail, name='operateur-detail'),
path('api/login/', api_login, name='api_login'),
    path('api/user-role/', get_user_role, name='user_role'),
    path('api/incidents/<int:incident_id>/acquit', acquit_incident, name='acquit_incident'),
path('api/incidents/active', get_active_incidents, name='get_active_incidents'),
path('api/logout/', api_logout, name='api_logout'),
path('api/sensors-data/', get_sensors_data, name='get_sensors_data'),
    path('api/sensors-details/<int:id>/', get_sensor_details, name='get_sensors_details'),
    path('api/sensors/', add_sensor, name='add_sensor'),
    path('api/sensors/<int:id>/', edit_sensor, name='edit_sensor'),
    path('api/sensors/delete/<int:id>/', delete_sensor, name='delete_sensor'),
path('api/incidents-history/', get_incidents_history, name='incidents_history'),
    path('api/incidents/<int:incident_id>/details/', get_incident_details, name='incident_details'),
path('api/add-enregistrement/', add_enregistrement, name='add-enregistrement'),
path('api/capteurs-list/', get_capteurs_list, name='capteurs-list'),
path('api/sensor-data/', get_sensor_with_latest_data, name='sensor-data'),
]