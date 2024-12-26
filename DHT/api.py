from .models import Enregistrement  # Replace Dht11 with Enregistrement
from .serializers import EnregistrementSerializer  # Update serializer name
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from twilio.rest import Client
from django.core.mail import send_mail
from django.conf import settings
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Function to send a WhatsApp alert
def send_whatsapp_alert(temp):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=f'Il y a une alerte importante sur votre capteur: la température ({temp}°C) dépasse le seuil.',
        to='whatsapp:+212641637040'
    )
    print(f"WhatsApp message sent: {message.sid}")

# Function to send a Telegram message
def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response

# API View for handling GET and POST requests
@api_view(["GET", "POST"])
def Dlist(request):
    if request.method == "GET":
        all_data = Enregistrement.objects.all()  # Use Enregistrement model
        data_ser = EnregistrementSerializer(all_data, many=True)  # Update serializer
        return Response(data_ser.data)

    elif request.method == "POST":
        serial = EnregistrementSerializer(data=request.data)  # Update serializer
        if serial.is_valid():
            serial.save()

            temp = serial.validated_data['temperature']  # Use the updated field name
            if temp > 100:  # Trigger alerts if the temperature exceeds the threshold

                # Send WhatsApp alert
                send_whatsapp_alert(temp)

                # Send email alert
                subject = 'Alerte'
                message = f'La température ({temp}°C) dépasse le seuil de 10°C. Veuillez intervenir immédiatement pour vérifier et corriger cette situation.'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = ['lamyaeouladali@gmail.com']
                send_mail(subject, message, email_from, recipient_list)

                # Send Telegram alert
                telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                telegram_message = f'La température ({temp}°C) dépasse le seuil de 10°C. Veuillez intervenir immédiatement pour vérifier et corriger cette situation.'
                send_telegram_message(telegram_token, chat_id, telegram_message)

            return Response(serial.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def enregistrement_list(request):
    enregistrements = Enregistrement.objects.all().order_by('-date_enregistrement')  # Latest first
    serializer = EnregistrementSerializer(enregistrements, many=True)
    return Response(serializer.data)