from rollbar.contrib.django.middleware import RollbarNotifierMiddleware


class CustomRollbarNotifierMiddleware(RollbarNotifierMiddleware):
    def get_payload_data(self, request, exc):
        payload_data = dict()

        if not request.user.is_anonymous:
            payload_data = {
                'person': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                },
            }

        return payload_data
