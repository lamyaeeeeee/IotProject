from .models import Enregistrement, Incident,Capteur, Alerte, Utilisateur, TemperatureThreshold
from .serializers import EnregistrementSerializer  # Update serializer name
from .models import TemperatureThreshold
from .serializers import TemperatureThresholdSerializer
from .models import OperatorAssignment
from .serializers import OperatorAssignmentSerializer
from .models import Utilisateur
from .serializers import UtilisateurSerializer
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from twilio.rest import Client
from django.core.mail import send_mail
from django.conf import settings
import requests
from dotenv import load_dotenv
from twilio.base.exceptions import TwilioRestException
import os
import time
from datetime import timedelta
from django.utils.timezone import now
from threading import Lock

alert_lock = Lock()
load_dotenv()

is_escalation_running = False
ESCALATION_DELAY_MINUTES = 1
def format_alert_message(temp, temp_state):
    return f'The temperature ({temp}°C) is in a state: {temp_state}. Please take immediate action.'


# Function to send a WhatsApp alert
def send_whatsapp_alert(message, phone_number):
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        whatsapp_message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=message,
            to=f'whatsapp:{phone_number}'
        )
        print(f"WhatsApp message sent: {whatsapp_message.sid}")
    except Exception as e:
        print(f"WhatsApp Error: {e}")






def send_telegram_message(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(url, data=payload)
        print(f"Telegram message sent: {response.status_code}")
    except Exception as e:
        print(f"Telegram Error: {e}")



def get_temperature_state(temp, thresholds):
    """
    Determine the state of the temperature based on database thresholds.
    Returns: "Normal Temperature", "Critical Temperature", or "Severe Temperature"
    """
    try:
        for threshold in thresholds:
            if threshold.label == "Normal Temperature Range" and threshold.min_value <= temp <= threshold.max_value:
                return "Normal Temperature"
            elif threshold.label.startswith("Critical") and threshold.min_value <= temp <= threshold.max_value:
                return "Critical Temperature"
        return "Severe Temperature"
    except Exception as e:
        print(f"Error determining temperature state: {e}")
        return "Error"


@api_view(["POST"])
def Dlist(request):
    """
    Gère les enregistrements de température et déclenche des alertes en fonction des seuils.
    """
    serial = EnregistrementSerializer(data=request.data)
    if serial.is_valid():
        # Étape 1 : Enregistrer la donnée
        enregistrement = serial.save()
        temp = serial.validated_data['temperature']
        capteur = serial.validated_data['id_capteur']
        thresholds = TemperatureThreshold.objects.all()
        temp_state = get_temperature_state(temp, thresholds)

        print(f"Temperature recorded: {temp}°C - State: {temp_state}")

        with alert_lock:  # Empêcher des exécutions concurrentes
            # Étape 2 : Déterminer le type d'incident
            type_incident = None
            if temp_state == "Critical Temperature":
                type_incident = "critical"
            elif temp_state == "Severe Temperature":
                type_incident = "severe"

            # Étape 3 : Vérifier ou créer un incident
            incident, created = Incident.objects.get_or_create(
                id_capteur=capteur,
                statut_incident='Active',
                defaults={
                    'temperature_detectee': temp,
                    'debut_incident': now(),
                    'type_incident': type_incident,  # Enregistrer le type d'incident
                }
            )

            if not created:
                # Mettre à jour la température détectée et le type d'incident
                incident.temperature_detectee = temp
                incident.type_incident = type_incident
                incident.save()

            # Étape 4 : Gérer les alertes
            if temp_state in ["Critical Temperature", "Severe Temperature"]:
                print(f"Processing alerts for incident: {incident.id_incident}")

                # Récupérer le premier opérateur
                first_operator = Utilisateur.objects.filter(role='technician').first()
                if first_operator:
                    # Mettre à jour le responsable dans l'incident
                    update_incident_responsible(incident, first_operator)

                    # Envoyer immédiatement la première alerte
                    if not Alerte.objects.filter(
                        id_incident=incident,
                        id_utilisateur=first_operator,
                        date_alerte__gte=now() - timedelta(seconds=10)  # Éviter les doublons récents
                    ).exists():
                        send_alerts(first_operator, f"Alerte initiale : Incident {incident.id_capteur.nom_capteur} avec {incident.temperature_detectee}°C")
                        Alerte.objects.create(
                            id_incident=incident,
                            id_utilisateur=first_operator,
                            niveau_alerte=1,
                            date_alerte=now()
                        )
                        print(f"Première alerte envoyée à {first_operator.nom}.")

                # Lancer le suivi des alertes
                start_alert_timer(incident, first_operator)

            else:
                # Si la température est normale, acquitter les incidents actifs
                Incident.objects.filter(id_capteur=capteur, statut_incident='Active').update(
                    statut_incident='Acknowledged',
                    fin_incident=now()
                )
                print(f"Temperature is back to normal for sensor {capteur.nom_capteur}. Incidents acknowledged.")

        return Response(serial.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)


import threading

def start_alert_timer(incident, operator):
    """
    Gère l'envoi périodique des alertes toutes les minutes jusqu'à atteindre la limite max_alerts.
    """
    def alert_timer():
        num_alerts_sent = Alerte.objects.filter(id_incident=incident, id_utilisateur=operator).count()
        operator_assignment = OperatorAssignment.objects.filter(operator=operator).first()
        max_alerts = operator_assignment.max_alerts if operator_assignment else 3  # Par défaut, max_alerts = 3

        while num_alerts_sent < max_alerts and incident.statut_incident == 'Active':
            # Attendre 1 minute
            time.sleep(60)

            # Vérifier si l'incident est toujours actif
            incident.refresh_from_db()
            if incident.statut_incident != 'Active':
                print(f"Incident {incident.id_incident} terminé. Arrêt du suivi des alertes.")
                break

            # Envoyer une nouvelle alerte
            num_alerts_sent += 1
            send_alerts(operator, f"Rappel {num_alerts_sent} : Incident {incident.id_capteur.nom_capteur} avec {incident.temperature_detectee}°C")
            Alerte.objects.create(
                id_incident=incident,
                id_utilisateur=operator,
                niveau_alerte=num_alerts_sent,
                date_alerte=now()
            )
            print(f"Alerte {num_alerts_sent} envoyée à {operator.nom} pour l'incident {incident.id_incident}.")

    # Lancer le suivi des alertes dans un thread
    thread = threading.Thread(target=alert_timer, daemon=True)
    thread.start()


def send_email_alert(message, recipient_email):
    try:
        subject = "Temperature Alert"
        email_from = settings.EMAIL_HOST_USER
        send_mail(subject, message, email_from, [recipient_email])
        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Email Error: {e}")

def handle_alerts_for_incident(incident):
    with alert_lock:  # Empêche les exécutions concurrentes
        print(f"Traitement des alertes pour l'incident {incident.id_incident}")

        latest_alert = Alerte.objects.filter(id_incident=incident).order_by('-date_alerte').first()

        if latest_alert:
            current_operator = latest_alert.id_utilisateur
            operator_assignment = OperatorAssignment.objects.filter(operator=current_operator).first()

            if operator_assignment:
                max_alerts = operator_assignment.max_alerts
                num_alerts_sent = Alerte.objects.filter(id_incident=incident, id_utilisateur=current_operator).count()
                time_since_last_alert = now() - latest_alert.date_alerte

                if time_since_last_alert.total_seconds() >= ESCALATION_DELAY_MINUTES * 60:
                    if num_alerts_sent < max_alerts:
                        print(f"Envoi de l'alerte {num_alerts_sent + 1} à {current_operator.nom}")
                        send_alerts(current_operator, f"Rappel : Incident {incident.id_capteur.nom_capteur} avec {incident.temperature_detectee}°C")
                        Alerte.objects.create(
                            id_incident=incident,
                            id_utilisateur=current_operator,
                            niveau_alerte=num_alerts_sent + 1,
                            date_alerte=now()
                        )
                    else:
                        print(f"Limite atteinte pour {current_operator.nom}. Escalade.")
                        escalate_to_next_operator(incident, current_operator)
                else:
                    print("Temps insuffisant depuis la dernière alerte.")
        else:
            first_operator = Utilisateur.objects.filter(role='technician').first()
            if first_operator:
                send_alerts(first_operator, f"Alerte initiale : Incident {incident.id_capteur.nom_capteur} avec {incident.temperature_detectee}°C")
                update_incident_responsible(incident, first_operator)
                Alerte.objects.create(
                    id_incident=incident,
                    id_utilisateur=first_operator,
                    niveau_alerte=1,
                    date_alerte=now()
                )

# API Views (example)
@api_view(["GET"])
def get_active_incidents(request):
    try:
        incidents = Incident.objects.filter(statut_incident='Active')
        response_data = []
        for incident in incidents:
            latest_alert = Alerte.objects.filter(id_incident=incident).order_by('-date_alerte').first()
            response_data.append({
                'incident_id': incident.id_incident,
                'sensor': incident.id_capteur.nom_capteur,
                'detected_temperature': incident.temperature_detectee,
                'start_time': incident.debut_incident,
                'alerted_user': f"{latest_alert.id_utilisateur.nom} {latest_alert.id_utilisateur.prenom}" if latest_alert else "N/A",
            })
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def acquit_incident(request, incident_id):
    """
    Acknowledge an active incident and stop further alerts.
    """
    try:
        incident = Incident.objects.get(id_incident=incident_id, statut_incident='Active')
        incident.statut_incident = 'Acknowledged'
        incident.fin_incident = now()

        # Clear the responsible user upon acknowledgment
        update_incident_responsible(incident, None)

        incident.save()
        return Response({'message': 'Incident acknowledged successfully'}, status=status.HTTP_200_OK)
    except Incident.DoesNotExist:
        return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)



def notify_operator(incident):
    """
    Envoie une alerte à l'opérateur pour un incident donné.
    """
    # Récupérer la dernière alerte
    latest_alert = Alerte.objects.filter(id_incident=incident).order_by('-date_alerte').first()

    if latest_alert:
        current_operator = latest_alert.id_utilisateur
        operator_assignment = OperatorAssignment.objects.filter(operator=current_operator).first()

        if operator_assignment:
            max_alerts = operator_assignment.max_alerts
            num_alerts_sent = Alerte.objects.filter(id_incident=incident, id_utilisateur=current_operator).count()
            time_since_last_alert = now() - latest_alert.date_alerte

            if time_since_last_alert.total_seconds() >= ESCALATION_DELAY_MINUTES * 60:
                if num_alerts_sent < max_alerts:
                    # Envoyer une alerte
                    send_alerts(current_operator, f"Reminder: Incident {incident.id_capteur.nom_capteur} with {incident.temperature_detectee}°C")
                    Alerte.objects.create(
                        id_incident=incident,
                        id_utilisateur=current_operator,
                        niveau_alerte=num_alerts_sent + 1,
                        date_alerte=now()
                    )
                else:
                    escalate_to_next_operator(incident, current_operator)
    else:
        # Envoyer une première alerte
        first_operator = Utilisateur.objects.filter(role='technician').first()
        if first_operator:
            send_alerts(first_operator, f"Initial Alert: Incident {incident.id_capteur.nom_capteur} with {incident.temperature_detectee}°C")
            Alerte.objects.create(
                id_incident=incident,
                id_utilisateur=first_operator,
                niveau_alerte=1,
                date_alerte=now()
            )
def update_incident_responsible(incident, new_responsible):
    incident.responsable = new_responsible
    incident.save()


def escalate_to_next_operator(incident, current_operator):
    """
    Escalates the incident to the next operator.
    """
    try:
        roles = ['technician', 'manager', 'CEO']
        current_role_index = roles.index(current_operator.role)
        next_role = roles[current_role_index + 1] if current_role_index + 1 < len(roles) else None

        if next_role:
            next_operator = Utilisateur.objects.filter(role=next_role).first()
            if next_operator:
                # Vérifier si une alerte récente a déjà été envoyée à ce niveau
                if not Alerte.objects.filter(
                        id_incident=incident,
                        id_utilisateur=next_operator,
                        date_alerte__gte=now() - timedelta(seconds=10)  # Vérifie les alertes récentes
                ).exists():
                    alert_message = f"Escalation Alert: Incident {incident.id_capteur.nom_capteur} with {incident.temperature_detectee}°C."

                    # Envoyer l'alerte
                    send_alerts(next_operator, alert_message)
                    print(f"Escalation alert sent to {next_operator.nom} ({next_role}).")

                    # Mettre à jour l'utilisateur responsable dans l'incident
                    update_incident_responsible(incident, next_operator)

                    # Créer une nouvelle alerte pour cet opérateur
                    Alerte.objects.create(
                        id_incident=incident,
                        id_utilisateur=next_operator,
                        niveau_alerte=1,
                        date_alerte=now()
                    )
                else:
                    print(
                        f"Alerte d'escalade déjà envoyée récemment à {next_operator.nom} ({next_role}). Pas d'envoi supplémentaire.")
            else:
                print(f"Aucun opérateur trouvé pour le rôle {next_role}.")
        else:
            print("Aucun rôle supérieur disponible pour escalade.")
    except Exception as e:
        print(f"Erreur lors de l'escalade pour l'incident {incident.id_incident}: {e}")


def send_alerts(operator, message):
    """
    Envoie les alertes via WhatsApp, Telegram et email.
    """
    if operator.telephone:
        send_whatsapp_alert(message, operator.telephone)
    if operator.id_telegram:
        send_telegram_message(os.getenv('TELEGRAM_BOT_TOKEN'), operator.id_telegram, message)
    if operator.email:
        send_email_alert(message, operator.email)



@api_view(['GET'])
def enregistrement_list(request):
    enregistrements = Enregistrement.objects.all().order_by('-date_enregistrement')  # Latest first
    serializer = EnregistrementSerializer(enregistrements, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def temperature_thresholds(request):
    if request.method == 'GET':
        thresholds = TemperatureThreshold.objects.all()
        serializer = TemperatureThresholdSerializer(thresholds, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Clear existing thresholds
        TemperatureThreshold.objects.all().delete()

        # Create new thresholds
        for threshold_data in request.data:
            serializer = TemperatureThresholdSerializer(data=threshold_data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Thresholds updated successfully'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_operators(request):
    technician = Utilisateur.objects.filter(role='technician').first()
    manager = Utilisateur.objects.filter(role='manager').first()

    operators = {
        'technician': UtilisateurSerializer(technician).data if technician else None,
        'manager': UtilisateurSerializer(manager).data if manager else None
    }
    return Response(operators)


@api_view(['GET', 'POST'])
def operator_assignments(request):
    if request.method == 'GET':
        assignments = OperatorAssignment.objects.all()
        serializer = OperatorAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Clear existing assignments
        OperatorAssignment.objects.all().delete()

        for assignment_data in request.data:
            serializer = OperatorAssignmentSerializer(data=assignment_data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Assignments updated successfully'}, status=status.HTTP_201_CREATED)




is_escalation_running = False  # Indicateur global pour empêcher les exécutions multiples

def start_escalation_task():
    global is_escalation_running

    if is_escalation_running:
        print("Escalation task already running.")
        return  # Empêche une nouvelle exécution si la tâche est déjà en cours

    is_escalation_running = True  # Marque la tâche comme en cours

    try:
        while True:
            with alert_lock:  # Empêche les exécutions concurrentes
                try:
                    print("Checking for escalations...")

                    # Récupérer les incidents actifs
                    incidents = Incident.objects.filter(statut_incident='Active').order_by('-debut_incident')
                    print(f"Active incidents: {[incident.id_incident for incident in incidents]}")

                    for incident in incidents:
                        # Gérer l'escalade si nécessaire
                        latest_alert = Alerte.objects.filter(id_incident=incident).order_by('-date_alerte').first()

                        if latest_alert:
                            current_operator = latest_alert.id_utilisateur
                            # Vérifier et gérer les alertes
                            handle_alert_for_operator(incident, current_operator)
                        else:
                            # Envoyer une première alerte si aucune n'a été envoyée
                            first_operator = Utilisateur.objects.filter(role='technician').first()
                            if first_operator:
                                send_alerts(first_operator,
                                            f"Initial Alert: Incident {incident.id_capteur.nom_capteur} with {incident.temperature_detectee}°C")
                                Alerte.objects.create(
                                    id_incident=incident,
                                    id_utilisateur=first_operator,
                                    niveau_alerte=1,
                                    date_alerte=now()
                                )
                except Exception as e:
                    print(f"Error while handling escalations: {e}")

            time.sleep(ESCALATION_DELAY_MINUTES * 60)
    finally:
        is_escalation_running = False  # Réinitialise l'indicateur lorsque la tâche se termine

def handle_alert_for_operator(incident, current_operator):
    """
    Gère l'envoi des alertes ou l'escalade pour un opérateur spécifique.
    """
    operator_assignment = OperatorAssignment.objects.filter(operator=current_operator).first()

    if operator_assignment:
        max_alerts = operator_assignment.max_alerts
        num_alerts_sent = Alerte.objects.filter(id_incident=incident, id_utilisateur=current_operator).count()
        time_since_last_alert = now() - Alerte.objects.filter(
            id_incident=incident, id_utilisateur=current_operator
        ).order_by('-date_alerte').first().date_alerte

        if time_since_last_alert.total_seconds() >= ESCALATION_DELAY_MINUTES * 60:
            if num_alerts_sent < max_alerts:
                send_alerts(current_operator,
                            f"Reminder: Incident {incident.id_capteur.nom_capteur} with {incident.temperature_detectee}°C")
                Alerte.objects.create(
                    id_incident=incident,
                    id_utilisateur=current_operator,
                    niveau_alerte=num_alerts_sent + 1,
                    date_alerte=now()
                )
            else:
                escalate_to_next_operator(incident, current_operator)



@api_view(['GET'])
def get_sensor_with_latest_data(request):
    try:
        # Get the latest sensor and log the result
        sensor = Capteur.objects.order_by('-id_capteur').first()
        if not sensor:
            print("No sensor found in database")
            return Response({'error': 'No sensors found in database'}, status=404)

        print(f"Found sensor: ID={sensor.id_capteur}, Name={sensor.nom_capteur}")

        # Get the latest reading for this sensor
        latest_reading = Enregistrement.objects.filter(
            id_capteur=sensor
        ).order_by('-date_enregistrement').first()

        if not latest_reading:
            print(f"No readings found for sensor {sensor.id_capteur}")
            return Response({
                'error': f'No readings found for sensor {sensor.id_capteur}'
            }, status=404)

        print(f"Found reading: Temp={latest_reading.temperature}, Humidity={latest_reading.humidite}")

        data = {
            'sensor': {
                'id': sensor.id_capteur,
                'name': sensor.nom_capteur,
                'latitude': sensor.latitude,
                'longitude': sensor.longitude,
            },
            'latest_reading': {
                'temperature': latest_reading.temperature,
                'humidity': latest_reading.humidite,
                'timestamp': latest_reading.date_enregistrement
            }
        }
        return Response(data)

    except Exception as e:
        print(f"Error in get_sensor_with_latest_data: {str(e)}")
        return Response({'error': str(e)}, status=500)