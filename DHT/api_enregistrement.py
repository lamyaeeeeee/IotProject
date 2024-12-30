from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Capteur, Enregistrement
from .serializers import CapteurSerializer, EnregistrementSerializer
from .models import Enregistrement, Incident, TemperatureThreshold
from .serializers import EnregistrementSerializer
from django.utils.timezone import now
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from datetime import timedelta
from .models import Enregistrement, Incident, Capteur, Alerte, Utilisateur, TemperatureThreshold
from .serializers import EnregistrementSerializer
from .models import TemperatureThreshold
from .models import OperatorAssignment  # Utilisé si nécessaire pour les rappels
from .models import Utilisateur
from .models import Alerte
from .serializers import UtilisateurSerializer
from threading import Lock
from .api import send_alerts, update_incident_responsible, get_temperature_state, start_alert_timer

@api_view(['GET'])
def get_capteurs_list(request):
    capteurs = Capteur.objects.all()
    serializer = CapteurSerializer(capteurs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def add_enregistrement(request):
    """
    Ajoute un enregistrement, vérifie les seuils, déclenche un incident si nécessaire,
    et envoie des alertes directement en utilisant les fonctions existantes.
    """
    serializer = EnregistrementSerializer(data=request.data)
    if serializer.is_valid():
        # Étape 1 : Sauvegarder l'enregistrement
        enregistrement = serializer.save()

        # Étape 2 : Récupérer les seuils de température
        thresholds = TemperatureThreshold.objects.all()
        temp = enregistrement.temperature
        capteur = enregistrement.id_capteur

        # Étape 3 : Déterminer l'état de la température
        temp_state = get_temperature_state(temp, thresholds)

        # Étape 4 : Vérifier ou créer un incident
        if temp_state in ["Critical Temperature", "Severe Temperature"]:
            type_incident = "critical" if temp_state == "Critical Temperature" else "severe"

            incident, created = Incident.objects.get_or_create(
                id_capteur=capteur,
                statut_incident="Active",
                defaults={
                    'temperature_detectee': temp,
                    'debut_incident': now(),
                    'type_incident': type_incident
                }
            )
            if not created:
                # Mettre à jour un incident existant
                incident.temperature_detectee = temp
                incident.type_incident = type_incident
                incident.save()

            print(f"Incident détecté: Capteur {capteur.nom_capteur}, Température {temp}°C, Type: {type_incident}")

            # Étape 5 : Gérer l'envoi des alertes
            first_operator = Utilisateur.objects.filter(role='technician').first()
            if first_operator:
                # Mettre à jour le responsable de l'incident
                update_incident_responsible(incident, first_operator)

                # Vérifier si une alerte a déjà été envoyée récemment
                if not Alerte.objects.filter(
                        id_incident=incident,
                        id_utilisateur=first_operator,
                        date_alerte__gte=now() - timedelta(seconds=10)
                ).exists():
                    send_alerts(
                        first_operator,
                        f"Initial Alert: Incident detected on {incident.id_capteur.nom_capteur}. "
                        f"Temperature: {incident.temperature_detectee}°C. "
                        f"Incident Type: {incident.type_incident.capitalize()}."
                    )
                    Alerte.objects.create(
                        id_incident=incident,
                        id_utilisateur=first_operator,
                        niveau_alerte=1,
                        date_alerte=now()
                    )
                    print(f"Alerte envoyée à {first_operator.nom}.")

            # Optionnel : Lancer le suivi des alertes
            start_alert_timer(incident, first_operator)
        else:
            print(f"Aucune alerte requise. Température normale pour {capteur.nom_capteur}.")

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
