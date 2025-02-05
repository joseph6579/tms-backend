import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users.api.serializers.users import UserCreateSerializer, UserSerializer
from users.tasks import send_user_registration_email
from users.utils import generate_random_string

User = get_user_model()

class UsersModelViewset(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_serializer_class(self):
        serializers = {
            'create': UserCreateSerializer
        }
        return serializers.get(self.action, super().get_serializer_class())

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        pwd = generate_random_string(length=12)
        user.organisation = serializer.validated_data.get('organisation', self.request.user.organisation)
        if not user.organisation:
            return Response({'detail': 'Organisation is required'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(pwd)
        user.save(update_fields=['password', 'organisation'])
        send_user_registration_email.apply_async(args=[user.id, pwd])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class Google(APIView):
    def get(self, request):
        return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({'detail': 'Not implemented'}, status=status.HTTP_501_NOT_IMPLEMENTED)
    def posting(self, request):
        """
        Get code from Google and return user data
        :param request:
        :return:
        """
        code = request.data.get('code', None)
        scope = request.data.get('scope', None)

        if not code:
            return Response({'detail': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Exchange Code for Token
        url = 'https://oauth2.googleapis.com/token'
        data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': code
        }
        response = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if response.status_code != 200:
            return Response({'detail': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)
        print(f'The response is: {response.json()}')
        token = response.json().get('access_token')
        # Get User Data
        url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        user_response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
        if user_response.status_code != 200:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        user_data = user_response.json()
        print(f'The user data is: {user_data}')
        return Response(user_data, status=status.HTTP_200_OK)
        # email = user_data.get('email', None)
        # if not email:
        #     return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        # user, created = User.objects.get_or_create(email=email)
        # if created:
        #     user.first_name = user_data.get('given_name', '')
        #     user.last_name = user_data.get('family_name', '')
        #     user.save()
        # return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

