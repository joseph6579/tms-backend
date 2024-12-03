from django.utils.crypto import get_random_string


def generate_random_string(length=8):
    return get_random_string(length)