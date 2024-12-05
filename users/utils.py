from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

User = get_user_model()


def generate_random_string(length=8):
    return get_random_string(length)



def send_registration_email(user: User, pwd: str ): # type: ignore
    context = {
        'name': f'{user.first_name} {user.last_name}',
        'organisation': user.organisation.name,
        'email': user.email,
        'password': pwd,
        'action_url': settings.LOGIN_URL
    }
    message = render_to_string(template_name='auth/new_account.html', context=context)
    email = EmailMultiAlternatives(
        subject='Welcome to TMS!',
        body=message,
        to=[user.email],
        from_email=settings.DEFAULT_FROM_EMAIL
    )
    try:
        email.content_subtype = 'html'
        email.send()
    except Exception as e:
        print(e)
