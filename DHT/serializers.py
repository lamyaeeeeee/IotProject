from rest_framework import serializers
from .models import Enregistrement  # Import the updated model
from .models import TemperatureThreshold
from .models import Utilisateur, OperatorAssignment

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