from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Capteur, Enregistrement
from .serializers import CapteurSerializer, EnregistrementSerializer

@api_view(['GET'])
def get_capteurs_list(request):
    capteurs = Capteur.objects.all()
    serializer = CapteurSerializer(capteurs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def add_enregistrement(request):
    serializer = EnregistrementSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)