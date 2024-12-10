from django.contrib import admin
from .models import Utilisateur, Capteur, Enregistrement, Incident, Alerte

# Enregistrer les nouveaux modèles dans l'administration Django
admin.site.register(Utilisateur)
admin.site.register(Capteur)
admin.site.register(Enregistrement)
admin.site.register(Incident)
admin.site.register(Alerte)
