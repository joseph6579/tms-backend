from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users.api.serializers.users import UserCreateSerializer, UserSerializer
from users.tasks import send_user_registration_email
from users.utils import generate_random_string

User = get_user_model()

class Users(ModelViewSet):
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