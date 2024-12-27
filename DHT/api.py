from .models import Enregistrement, Capteur  # Replace Dht11 with Enregistrement
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

load_dotenv()


def format_alert_message(temp, temp_state):
    return f'The temperature ({temp}°C) is in a state: {temp_state}. Please take immediate action.'


# Function to send a WhatsApp alert
def send_whatsapp_alert(message):
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        client = Client(account_sid, auth_token)

        whatsapp_message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=message,
            to='whatsapp:+212641637040'
        )
        print(f"WhatsApp message sent: {whatsapp_message.sid}")
    except TwilioRestException as e:
        print(f"Twilio Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


# Function to send a Telegram message
def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response


def get_temperature_state(temp):
    """
    Determine the state of the temperature based on database thresholds.
    Returns: "Normal Temperature", "Critical Temperature", or "Severe Temperature"
    """
    try:
        thresholds = TemperatureThreshold.objects.all()

        # Check if temperature is in the normal range
        for threshold in thresholds:
            if threshold.label == "Normal Temperature Range" and threshold.min_value <= temp <= threshold.max_value:
                return "Normal Temperature"

        # Check if temperature is in any critical range
        for threshold in thresholds:
            if threshold.label.startswith("Critical") and threshold.min_value <= temp <= threshold.max_value:
                return "Critical Temperature"

        # If no range matches, it's a severe temperature
        return "Severe Temperature"
    except Exception as e:
        print(f"Error determining temperature state: {e}")
        return "Error"


@api_view(["GET", "POST"])
def Dlist(request):
    if request.method == "GET":
        all_data = Enregistrement.objects.all()  # Fetch all records
        data_ser = EnregistrementSerializer(all_data, many=True)  # Serialize data
        return Response(data_ser.data)

    elif request.method == "POST":
        serial = EnregistrementSerializer(data=request.data)  # Deserialize request data
        if serial.is_valid():
            serial.save()

            temp = serial.validated_data['temperature']  # Extract temperature
            temp_state = get_temperature_state(temp)

            # Format the message
            alert_message = format_alert_message(temp, temp_state)

            # Send notifications only for Critical or Severe cases
            if temp_state in ["Critical Temperature", "Severe Temperature"]:
                try:
                    # Send WhatsApp alert
                    send_whatsapp_alert(alert_message)

                    # Send email alert
                    subject = f'Alert - {temp_state}'
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = ['lamyaeouladali@gmail.com']
                    send_mail(subject, alert_message, email_from, recipient_list)

                    # Send Telegram alert
                    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                    chat_id = os.getenv('TELEGRAM_CHAT_ID')
                    send_telegram_message(telegram_token, chat_id, alert_message)
                except Exception as e:
                    print(f"Notification Error: {e}")
            else:
                print(f"No notification sent. Temperature ({temp}°C) is normal.")

            # Return serialized data
            return Response(serial.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(['GET'])
def get_sensor_with_latest_data(request):
    try:
        # Get the first sensor (since you're using only one)
        sensor = Capteur.objects.first()

        # Get the latest reading for this sensor
        latest_reading = Enregistrement.objects.filter(
            id_capteur=sensor
        ).order_by('-date_enregistrement').first()

        if sensor and latest_reading:
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
        return Response({'error': 'No sensor or readings found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)