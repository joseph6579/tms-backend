import uuid

from dispatch.constants import OrderStatusChoices
from dispatch.models import Location
from django.contrib.gis.geos import Point


def get_or_create_location(name: str, latitude: float, longitude: float, organisation_id: uuid) -> Location:
    point = Point(x=latitude, y=longitude)
    loc, _ = Location.objects.get_or_create(organisation_id=organisation_id, name=name, coordinates=point)
    return loc


def stop_type_to_order_status(stop_type: str) -> str:
    """
    Match a trip stop type to an order status
    :param stop_type:
    :return:
    """
    match stop_type:
        case 'pickup':
            return OrderStatusChoices.IN_TRANSIT.value
        case 'drop_off':
            return OrderStatusChoices.COMPLETED.value
        case default:
            return stop_type
