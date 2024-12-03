import uuid

from django.db import models

from commons.behaviour import CommonInfo

VEHICLE_SOURCES = (
    ('in_house', 'in_house'),
    ('third_party', 'third_party'),
)


class Vehicle(CommonInfo):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    registration_number = models.CharField(max_length=20, unique=True)
    driver = models.OneToOneField('users.Driver', on_delete=models.CASCADE, null=True, blank=True, related_name='vehicle')
    source = models.CharField(max_length=11, choices=VEHICLE_SOURCES, default='in_house')

    def __str__(self):
        return self.name
    


class VehicleAssignmentLogs(CommonInfo):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    vehicle = models.ForeignKey('fleet.Vehicle', on_delete=models.CASCADE)
    driver = models.ForeignKey('users.Driver', on_delete=models.CASCADE, related_name='vehicle_assignments')
    assigned_by = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='user_vehicle_assignments')

    class Meta:
        verbose_name = 'Vehicle Assignment Log'
        verbose_name_plural = 'Vehicle Assignment Logs'
