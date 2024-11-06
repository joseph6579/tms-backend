from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, action

from users.api.serializers.users import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class Users(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()