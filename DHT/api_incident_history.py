from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Incident, Alerte, Utilisateur
from .serializers import IncidentSerializer
from .serializers import AlerteSerializer
from django.db.models import Count


@api_view(['GET'])
def get_incidents_history(request):
    incidents = (Incident.objects.exclude(statut_incident__iexact='Active')
                .select_related('id_capteur')
                .order_by('-debut_incident'))
    serializer = IncidentSerializer(incidents, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_incident_details(request, incident_id):
    # Get alert count
    alert_count = Alerte.objects.filter(id_incident=incident_id).count()
    
    # Get alerts with related user info
    alerts = (Alerte.objects.filter(id_incident=incident_id)
             .select_related('id_utilisateur', 'id_incident')
             .order_by('-date_alerte'))
    
    # Custom serialization to include user details
    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            'id_alerte': alert.id_alerte,
            'date_alerte': alert.date_alerte,
            'niveau_alerte': alert.niveau_alerte,
            'operator': f"{alert.id_utilisateur.nom} {alert.id_utilisateur.prenom}"
        })
    
    return Response({
        'alert_count': alert_count,
        'alerts': alerts_data
    })