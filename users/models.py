from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


USER_ROLES = (
    ('admin', 'Admin'),
    ('staff', 'staff'),
)


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, editable=False)
    username = None
    email = models.EmailField(_('email address'), unique=True)
    organisation = models.ForeignKey('organisations.Organisation', on_delete=models.CASCADE)
    role = models.CharField(choices=USER_ROLES, max_length=10, default='staff')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'





