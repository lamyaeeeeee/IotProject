from rest_framework import serializers
from .models import Enregistrement  # Import the updated model
from .models import  Utilisateur
class EnregistrementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enregistrement
        fields = '__all__'
        extra_kwargs = {
            'date_enregistrement': {'required': False},
        }
class OperateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = '__all__'