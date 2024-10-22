from django.db import models
from commons.behaviour import CommonInfo


class Organisation(CommonInfo):
    name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name
