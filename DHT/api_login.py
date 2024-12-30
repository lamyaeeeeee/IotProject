from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Utilisateur
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@api_view(["POST"])
def api_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'message': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = Utilisateur.objects.get(email=email)

        if password == user.mot_de_passe:
            # Créer une session
            request.session['user_id'] = user.id_utilisateur
            request.session['role'] = user.role
            request.session.save()  # Important pour sauvegarder la session

            response = Response(
                {'message': 'Login successful', 'role': user.role},
                status=status.HTTP_200_OK
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            return response
        else:
            return Response(
                {'message': 'Invalid password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    except Utilisateur.DoesNotExist:
        return Response(
            {'message': 'User does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )


@login_required
def get_user_role(request):
    if request.user.is_authenticated:
        # Safely retrieve the user's first group
        group = request.user.groups.first()
        if group:  # Check if the user belongs to a group
            return JsonResponse({'role': group.name}, safe=False)
        else:
            return JsonResponse({'role': 'No group assigned'}, safe=False)  # Handle no group case
    return JsonResponse({'error': 'User not authenticated'}, status=403)
