from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from dispatch.api.serializers.orders import OrderWriteSerializer
from dispatch.models import Order, Location
from organisations.models import Store

User = get_user_model()


class OrderWriteSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@leta.ai', password='test123')
        self.organisation = self.user.organisation
        self.user.organisation = self.organisation
        self.user.save()

        self.factory = APIRequestFactory()
        self.request = self.factory.post('/fake-url')
        self.request.user = self.user

        self.pickup = {'name': 'Pickup Location', 'latitude': -1.2921, 'longitude': 36.8219}
        self.drop_off = {'name': 'Drop Off Location', 'latitude': -1.2922, 'longitude': 36.8220}
        self.store = Store.objects.create(
            name='Main Store', key='main-store', organisation=self.organisation, location=Point(36.8219, -1.2921)
        )

    def test_valid_order_minimal_data(self):
        payload = {
            'reference_number': 'ORDER-001',
            'pickup': self.pickup,
            'drop_off': self.drop_off,
            'description': 'Test Order',
            'instructions': 'Handle with care',
            'priority': 'normal',
            'recipient_name': 'John Doe',
            'recipient_email': 'john@example.com',
        }
        serializer = OrderWriteSerializer(data=payload, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        validated = serializer.validated_data
        self.assertIn('recipient', validated)
        self.assertEqual(validated['recipient'].name, 'John Doe')

    def test_missing_contact_details_raises_error(self):
        payload = {
            'reference_number': 'ORDER-002',
            'pickup': self.pickup,
            'drop_off': self.drop_off,
            'description': 'Test Order',
            'instructions': 'Handle with care',
            'priority': 'normal',
            'recipient_name': 'John Doe',
        }
        serializer = OrderWriteSerializer(data=payload, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_existing_reference_number_raises_error(self):
        Order.objects.create(
            reference_number='DUPLICATE',
            organisation=self.organisation,
            pickup=Location.objects.create(name='Loc 1', coordinates=Point(0, 0)),
            drop_off=Location.objects.create(name='Loc 2', coordinates=Point(1, 1)),
        )
        payload = {
            'reference_number': 'DUPLICATE',
            'pickup': self.pickup,
            'drop_off': self.drop_off,
            'description': 'Duplicate Test',
            'instructions': 'Test',
            'priority': 'normal',
            'recipient_name': 'Jane Doe',
            'recipient_email': 'jane@example.com',
        }
        serializer = OrderWriteSerializer(data=payload, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('reference_number', serializer.errors)

    def test_invalid_store_key(self):
        payload = {
            'reference_number': 'ORDER-KEY',
            'pickup': self.pickup,
            'drop_off': self.drop_off,
            'description': 'Invalid Store Key',
            'instructions': 'N/A',
            'priority': 'normal',
            'recipient_name': 'Buyer X',
            'recipient_email': 'buyerx@example.com',
            'store_key': 'unknown-store',
        }
        serializer = OrderWriteSerializer(data=payload, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('store_key', serializer.errors)

    def test_valid_buyer_info(self):
        payload = {
            'reference_number': 'ORDER-003',
            'pickup': self.pickup,
            'drop_off': self.drop_off,
            'description': 'Test with Buyer',
            'instructions': 'Handle well',
            'priority': 'normal',
            'recipient_name': 'Recipient X',
            'recipient_email': 'recipientx@example.com',
            'buyer_name': 'Buyer Y',
            'buyer_email': 'buyery@example.com',
        }
        serializer = OrderWriteSerializer(data=payload, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        validated = serializer.validated_data
        self.assertIn('buyer', validated)
        self.assertEqual(validated['buyer'].name, 'Buyer Y')

    def test_valid_store_key(self):
        payload = {
            'reference_number': 'ORDER-004',
            'pickup': self.pickup,
            'drop_off': self.drop_off,
            'description': 'Store Order',
            'instructions': 'No instructions',
            'priority': 'normal',
            'recipient_name': 'Recipient Y',
            'recipient_phone_number': '0712345678',
            'store_key': 'main-store',
        }
        serializer = OrderWriteSerializer(data=payload, context={'request': self.request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        validated = serializer.validated_data
        self.assertIn('store', validated)
        self.assertEqual(validated['store'].id, self.store.id)
