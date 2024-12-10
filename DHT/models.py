from django.db import models

class Utilisateur(models.Model):
    id_utilisateur = models.BigAutoField(primary_key=True)
    nom = models.TextField()
    prenom = models.TextField()
    email = models.TextField(unique=True)
    telephone = models.TextField(null=True, blank=True)
    mot_de_passe = models.TextField()
    role = models.TextField()
    token = models.TextField(null=True, blank=True)
    id_telegram = models.TextField(unique=True, null=True, blank=True)

class Capteur(models.Model):
    id_capteur = models.BigAutoField(primary_key=True)
    nom_capteur = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()

class Enregistrement(models.Model):
    id_enregistrement = models.BigAutoField(primary_key=True)
    id_capteur = models.ForeignKey(Capteur, on_delete=models.CASCADE)
    temperature = models.FloatField()
    humidite = models.FloatField()
    date_enregistrement = models.DateTimeField(auto_now_add=True)

class Incident(models.Model):
    id_incident = models.BigAutoField(primary_key=True)
    id_capteur = models.ForeignKey(Capteur, on_delete=models.CASCADE)
    temperature_detectee = models.FloatField()
    debut_incident = models.DateTimeField()
    fin_incident = models.DateTimeField(null=True, blank=True)
    statut_incident = models.TextField()

class Alerte(models.Model):
    id_alerte = models.BigAutoField(primary_key=True)
    id_incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    id_utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_alerte = models.DateTimeField(auto_now_add=True)
    niveau_alerte = models.IntegerField()
