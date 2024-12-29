from django.shortcuts import render
from .models import Enregistrement  # Import the new model
from django.utils import timezone
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth import logout
from django.views.generic import TemplateView

def home(request):
    # Instead of looking for home.html, serve the React index.html
    return TemplateView.as_view(template_name='index.html')(request)

def table(request):
    derniere_ligne = Enregistrement.objects.last()  # Use Enregistrement model
    if derniere_ligne:
        derniere_date = derniere_ligne.date_enregistrement
        delta_temps = timezone.now() - derniere_date
        difference_minutes = delta_temps.seconds // 60
        temps_ecoule = f'il y a {difference_minutes} min'
        if difference_minutes > 60:
            temps_ecoule = f'il y a {difference_minutes // 60}h {difference_minutes % 60}min'
        valeurs = {
            'date': temps_ecoule,
            'id': derniere_ligne.id_enregistrement,
            'temp': derniere_ligne.temperature,
            'hum': derniere_ligne.humidite
        }
    else:
        valeurs = {'date': 'Aucune donnée disponible', 'id': None, 'temp': None, 'hum': None}
    return render(request, 'value.html', {'valeurs': valeurs})


def download_csv(request):
    model_values = Enregistrement.objects.all()  # Use Enregistrement model
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="enregistrements.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'temperature', 'humidity', 'date_enregistrement'])
    liste = model_values.values_list('id_enregistrement', 'temperature', 'humidite', 'date_enregistrement')
    for row in liste:
        writer.writerow(row)
    return response


def index_view(request):
    return render(request, 'index.html')


def graphiqueTemp(request):
    return render(request, 'ChartTemp.html')


def graphiqueHum(request):
    return render(request, 'ChartHum.html')


def chart_data(request):
    enregistrements = Enregistrement.objects.all()  # Use Enregistrement model
    data = {
        'temps': [enregistrement.date_enregistrement for enregistrement in enregistrements],
        'temperature': [enregistrement.temperature for enregistrement in enregistrements],
        'humidity': [enregistrement.humidite for enregistrement in enregistrements]
    }
    return JsonResponse(data)


def chart_data_jour(request):
    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)
    enregistrements = Enregistrement.objects.filter(date_enregistrement__range=(last_24_hours, now))
    data = {
        'temps': [enregistrement.date_enregistrement for enregistrement in enregistrements],
        'temperature': [enregistrement.temperature for enregistrement in enregistrements],
        'humidity': [enregistrement.humidite for enregistrement in enregistrements]
    }
    return JsonResponse(data)


def chart_data_semaine(request):
    date_debut_semaine = timezone.now().date() - timedelta(days=7)
    enregistrements = Enregistrement.objects.filter(date_enregistrement__gte=date_debut_semaine)
    data = {
        'temps': [enregistrement.date_enregistrement for enregistrement in enregistrements],
        'temperature': [enregistrement.temperature for enregistrement in enregistrements],
        'humidity': [enregistrement.humidite for enregistrement in enregistrements]
    }
    return JsonResponse(data)


def chart_data_mois(request):
    date_debut_mois = timezone.now().date() - timedelta(days=30)
    enregistrements = Enregistrement.objects.filter(date_enregistrement__gte=date_debut_mois)
    data = {
        'temps': [enregistrement.date_enregistrement for enregistrement in enregistrements],
        'temperature': [enregistrement.temperature for enregistrement in enregistrements],
        'humidity': [enregistrement.humidite for enregistrement in enregistrements]
    }
    return JsonResponse(data)


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})
