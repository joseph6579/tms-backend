from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from string import digits

from users.models import Driver

User = get_user_model()


def generate_random_string(length=8):
    return get_random_string(length)


def generate_code(length: int = 4):
    """
    Generate a driver code
    :param length:
    :return:
    """
    return get_random_string(length=length, allowed_chars=digits)


def send_registration_email(user: User, pwd: str):  # type: ignore
    context = {
        'name': f'{user.first_name} {user.last_name}',
        'organisation': user.organisation.name,
        'email': user.email,
        'password': pwd,
        'action_url': settings.LOGIN_URL,
    }
    message = render_to_string(template_name='auth/new_account.html', context=context)
    email = EmailMultiAlternatives(
        subject='Welcome to TMS!', body=message, to=[user.email], from_email=settings.DEFAULT_FROM_EMAIL
    )
    try:
        email.content_subtype = 'html'
        email.send()
    except Exception as e:
        print(e)


def get_driver_by_email(email: str) -> UUID:
    return Driver.objects.only('email', 'id').filter(email=email).first()


def get_driver_by_phone(phone_number: str) -> UUID:
    return Driver.objects.only('phone_number', 'id').filter(phone_number=phone_number).first()
