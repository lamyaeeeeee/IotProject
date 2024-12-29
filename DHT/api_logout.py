from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(["POST"])
def api_logout(request):
    if request.method == "POST":
        # Clear the session
        request.session.flush()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    return Response({'message': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
