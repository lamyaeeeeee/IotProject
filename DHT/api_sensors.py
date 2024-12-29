from venv import logger
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Capteur, Enregistrement
from .serializers import CapteurSerializer


@api_view(["GET"])
def get_sensors_data(request):
    try:
        payload = request.data  # e.g., {"status": "Active"} or filter criteria
        sensors = Capteur.objects.all()  # Adjust based on filter criteria if needed

        result = []
        for sensor in sensors:
            last_record = Enregistrement.objects.filter(id_capteur=sensor).order_by('-date_enregistrement').first()
            result.append({
                "id": sensor.id_capteur,  # Keeping sensor ID for internal use
                "name": sensor.nom_capteur,  # Returning the name instead of the ID
                "latitude": sensor.latitude,
                "longitude": sensor.longitude,
                "lastReading": f"{last_record.temperature} - {last_record.humidite}" if last_record else "N/A",
            })
        return Response(result, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


@api_view(['GET'])
def get_sensor_details(request, id):
    try:
        sensor = Capteur.objects.get(id_capteur=id)
        last_record = Enregistrement.objects.filter(id_capteur=sensor).order_by('-date_enregistrement').first()

        return Response({
            "id": sensor.id_capteur,
            "name": sensor.nom_capteur,
            "latitude": sensor.latitude,
            "longitude": sensor.longitude,
            "lastReading": {
                "temperature": last_record.temperature if last_record else "N/A",
                "humidity": last_record.humidite if last_record else "N/A",
            },
            "status": True if last_record else False,
        })
    except Capteur.DoesNotExist:
        return Response({"error": "Sensor not found"}, status=404)


# Add a new sensor (POST)
@api_view(['POST'])
def add_sensor(request):
    try:
        logger.info(f"Incoming request data: {request.data}")
        serializer = CapteurSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Sensor added successfully", "data": serializer.data}, status=201)
        return Response(serializer.errors, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=400)


# Edit an existing sensor (PUT)
@api_view(['PUT'])
def edit_sensor(request, id):
    try:
        sensor = Capteur.objects.get(id_capteur=id)
        serializer = CapteurSerializer(sensor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Sensor updated successfully", "data": serializer.data}, status=200)
        return Response(serializer.errors, status=400)
    except Capteur.DoesNotExist:
        return Response({"error": "Sensor not found"}, status=404)


# Delete a sensor (DELETE)
@api_view(['DELETE'])
def delete_sensor(request, id):
    try:
        sensor = Capteur.objects.get(id_capteur=id)
        sensor.delete()
        return Response({"message": "Sensor deleted successfully"}, status=200)
    except Capteur.DoesNotExist:
        return Response({"error": "Sensor not found"}, status=404)