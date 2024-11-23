from .models import Dht11
from .serializers import DHT11serialize
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


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    return response

@api_view(["GET", "POST"])
def Dlist(request):
    if request.method == "GET":
        all_data = Dht11.objects.all()
        data_ser = DHT11serialize(all_data, many=True)
        return Response(data_ser.data)

    elif request.method == "POST":
        serial = DHT11serialize(data=request.data)
        if serial.is_valid():
            serial.save()


            temp = serial.validated_data['temp']
            if temp > 10:

                send_whatsapp_alert(temp)

                subject = 'Alerte'
                message = f'La température ({temp}°C) dépasse le seuil de 10°C. Veuillez intervenir immédiatement pour vérifier et corriger cette situation.'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = ['lamyaeouladali@gmail.com']
                send_mail(subject, message, email_from, recipient_list)

                telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                chat_id = os.getenv('TELEGRAM_CHAT_ID')
                telegram_message = f'La température ({temp}°C) dépasse le seuil de 10°C. Veuillez intervenir immédiatement pour vérifier et corriger cette situation.'
                send_telegram_message(telegram_token, chat_id, telegram_message)

            return Response(serial.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serial.errors, status=status.HTTP_400_BAD_REQUEST)
