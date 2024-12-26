from rest_framework import serializers
from .models import Enregistrement  # Import the updated model

class EnregistrementSerializer(serializers.ModelSerializer):  # Update serializer name
    class Meta:
        model = Enregistrement  # Use the updated model
        fields = '__all__'  # Include all fields of the Enregistrement model
