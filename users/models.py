import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.managers import CustomUserManager

USER_ROLES = (
    ('admin', 'admin'),
    ('staff', 'staff'),
    ('driver', 'driver')
)

DRIVER_STATUSES = (
    ('busy', 'busy'),
    ('available', 'available'),
    ('offline', 'offline'),
    ('inactive', 'inactive'),
)


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    username = None
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    email = models.EmailField(_('email address'), unique=True)
    organisation = models.ForeignKey('organisations.Organisation', on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(choices=USER_ROLES, max_length=10, default='staff')
    is_master_user = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    


class Driver(CustomUser):
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    status = models.CharField(max_length=10, default='active', choices=DRIVER_STATUSES)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    class Meta:
        verbose_name_plural = 'Drivers'
        verbose_name = 'Driver'
        ordering = ['-id']





