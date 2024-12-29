from rest_framework import serializers
from .models import Enregistrement  # Import the updated model
from .models import TemperatureThreshold
from .models import Utilisateur, OperatorAssignment
from .models import Incident, Alerte, Utilisateur
from .models import Capteur
class EnregistrementSerializer(serializers.ModelSerializer):  # Update serializer name
    class Meta:
        model = Enregistrement  # Use the updated model
        fields = '__all__'  # Include all fields of the Enregistrement model

class TemperatureThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemperatureThreshold
        fields = ['id_threshold', 'label', 'min_value', 'max_value']

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = ['id_utilisateur', 'nom', 'prenom', 'role']

class OperatorAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatorAssignment
        fields = ['id_assignment', 'operator', 'max_alerts']
class OperateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = '__all__'

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'

class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = '__all__'

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = '__all__'

class CapteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capteur
        fields = ['id_capteur', 'nom_capteur', 'latitude','longitude']
class IncidentSerializer(serializers.ModelSerializer):
    sensor = serializers.CharField(source='id_capteur.nom_capteur', read_only=True)  # Nom du capteur
    alerted_user = serializers.CharField(source='responsable.nom', read_only=True)  # Nom de l'utilisateur responsable

    class IncidentSerializer(serializers.ModelSerializer):
        sensor_id = serializers.IntegerField(source='id_capteur.id_capteur', read_only=True)

        class Meta:
            model = Incident
            fields = ['id_incident', 'sensor_id', 'temperature_detectee', 'debut_incident',
                      'fin_incident', 'statut_incident', 'type_incident','responsable']

    class AlerteSerializer(serializers.ModelSerializer):
        id_incident = IncidentSerializer()

        class Meta:
            model = Alerte
            fields = ['id_alerte', 'id_incident', 'id_utilisateur', 'date_alerte', 'niveau_alerte']
    class Meta:
        model = Incident
        fields = [
            'id_incident',
            'sensor',
            'temperature_detectee',
            'debut_incident',
            'fin_incident',
            'statut_incident',
            'alerted_user',
            'type_incident',
        ]

    def get_is_responsible(self, obj):
        request = self.context.get('request')
        return obj.responsable == request.user if request else False

