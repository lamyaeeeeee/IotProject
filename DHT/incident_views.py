from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Incident
from .serializers import IncidentSerializer
from django.utils.timezone import now
from .models import Utilisateur
from django.contrib.auth import authenticate, login
import logging
@api_view(['GET'])
def get_active_incidents(request):
    role = request.query_params.get('role')  # Récupérer le rôle depuis les paramètres
    if not role:
        return Response({"detail": "Role is missing."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        incidents = Incident.objects.filter(fin_incident__isnull=True)
        data = []

        for incident in incidents:
            serialized_incident = IncidentSerializer(incident).data
            # Ajouter is_responsible pour indiquer si l'utilisateur actuel est responsable
            serialized_incident['is_responsible'] = (
                incident.responsable and incident.responsable.role == role
            )
            # Ajouter le nom complet du responsable
            serialized_incident['responsable_full_name'] = (
                f"{incident.responsable.nom} {incident.responsable.prenom}"
                if incident.responsable else "No responsible assigned"
            )

            # Vérifier si type_incident est nul ou vide
            if not incident.type_incident:
                serialized_incident['type_incident'] = "Unknown"

            data.append(serialized_incident)

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logging.error(f"Error in get_active_incidents: {e}")
        return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def acquit_incident(request, incident_id):
    """
    Acquitte un incident en cours en utilisant la logique de rôle de l'utilisateur.
    """
    role = request.data.get('role')  # Récupérer le rôle depuis les données de la requête
    if not role:
        return Response(
            {"detail": "Role is missing."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Vérifier si l'incident existe
        incident = Incident.objects.get(id_incident=incident_id)

        # Vérifier si l'utilisateur a le rôle de responsable
        if incident.responsable and incident.responsable.role != role:
            return Response(
                {"detail": "You are not responsible for this incident."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Marquer l'incident comme terminé
        incident.fin_incident = now()
        incident.statut_incident = "Acknowledged"
        incident.save()

        return Response({"detail": "Incident acknowledged successfully."})
    except Incident.DoesNotExist:
        return Response(
            {"detail": "Incident not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

