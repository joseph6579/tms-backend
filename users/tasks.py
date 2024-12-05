from celery import shared_task
from django.contrib.auth import get_user_model


@shared_task
def send_user_registration_email(user_id: int, pwd: str):
    user_model = get_user_model()
    from users.utils import send_registration_email
    try:
        user = user_model.objects.get(id=user_id)
        send_registration_email(user=user, pwd=pwd)
    except user_model.DoesNotExist:
        return
    
    