from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_user_registration_email(user: User):
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from django.template.loader import render_to_string

    try:
        message = render_to_string('users/emails/registration.html', {'user': user})
        email = EmailMultiAlternatives(
            subject='Welcome to TMS',
            body=message,
            from_email=settings.EMAIL_HOST_USER,
            to=[user.email],
        )
        email.attach_alternative(message, 'text/html')
        email.send()
    except Exception as e:
        print(e)