import uuid
from dispatch.models import Location
from django.contrib.gis.geos import Point


def get_or_create_location(name: str, latitude: float, longitude: float, organisation_id: uuid) -> Location:
    point = Point(x=latitude, y=longitude)
    loc, _ = Location.objects.get_or_create(organisation_id=organisation_id, name=name, coordinates=point)
    return loc
