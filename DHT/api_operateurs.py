from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import  Utilisateur
from .serializers import OperateurSerializer

@api_view(['GET', 'POST'])
def operateur_list(request):
    if request.method == 'GET':
        operateurs =  Utilisateur.objects.all()
        serializer = OperateurSerializer(operateurs, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = OperateurSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def operateur_detail(request, pk):
    try:
        operateur =  Utilisateur.objects.get(pk=pk)
    except  Utilisateur.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = OperateurSerializer(operateur)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = OperateurSerializer(operateur, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        operateur.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)