from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import uuid

from organisations.models import OrganisationSubscription, Package
from organisations.api.serializers.subscriptions import OrganisationSubscriptionSerializer
from organisations.services.paystack import PaystackService
from organisations.permissions import IsOrganisationAdmin


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = OrganisationSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsOrganisationAdmin]
    paystack_service = PaystackService()

    def get_queryset(self):
        return OrganisationSubscription.objects.filter(organisation=self.request.user.organisation)

    @action(detail=False, methods=['post'])
    def initialize_payment(self, request):
        """Initialize payment for a subscription"""
        package_id = request.data.get('package_id')
        try:
            package = Package.objects.get(id=package_id)
        except Package.DoesNotExist:
            return Response({'detail': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create subscription record
        subscription = OrganisationSubscription.objects.create(
            organisation=request.user.organisation,
            package=package,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=package.duration_days),
            payment_reference=str(uuid.uuid4()),
        )

        # Initialize Paystack transaction
        amount_in_kobo = int(package.price * 100)  # Convert to kobo
        response = self.paystack_service.initialize_transaction(
            email=request.user.organisation.email,
            amount=amount_in_kobo,
            reference=subscription.payment_reference,
            metadata={'subscription_id': str(subscription.id), 'package_name': package.name},
        )

        if response.get('status'):
            return Response(
                {
                    'authorization_url': response['data']['authorization_url'],
                    'reference': subscription.payment_reference,
                }
            )
        return Response({'detail': 'Failed to initialize payment'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """Verify a subscription payment"""
        reference = request.data.get('reference')
        try:
            subscription = OrganisationSubscription.objects.get(
                payment_reference=reference, organisation=request.user.organisation
            )
        except OrganisationSubscription.DoesNotExist:
            return Response({'detail': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)

        response = self.paystack_service.verify_transaction(reference)

        if response.get('status') and response['data']['status'] == 'success':
            subscription.payment_status = 'paid'
            subscription.is_active = True
            subscription.save()

            return Response({'status': 'success', 'subscription': self.get_serializer(subscription).data})

        subscription.payment_status = 'failed'
        subscription.save()
        return Response({'detail': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription"""
        subscription = self.get_object()

        if not subscription.is_active:
            return Response({'detail': 'Subscription is not active'}, status=status.HTTP_400_BAD_REQUEST)

        subscription.is_active = False
        subscription.payment_status = 'cancelled'
        subscription.save()

        return Response({'status': 'subscription cancelled'})
