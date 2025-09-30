from rest_framework import serializers
from dispatch.models import Order, Location, Customer, OrderReview
from users.api.serializers.users import UserMiniSerializer

class LocationMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'city']

class CustomerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number']

class OrderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReview
        fields = ['id', 'order', 'driver', 'rating', 'driver_rating', 'comments']
        read_only_fields = ['reviewed_by']

    def create(self, validated_data):
        validated_data['reviewed_by'] = self.context['request'].user
        return super().create(validated_data)

class OrderSerializer(serializers.ModelSerializer):
    pickup_details = LocationMiniSerializer(source='pickup', read_only=True)
    drop_off_details = LocationMiniSerializer(source='drop_off', read_only=True)
    recipient_details = CustomerMiniSerializer(source='recipient', read_only=True)
    buyer_details = CustomerMiniSerializer(source='buyer', read_only=True)
    driver_details = UserMiniSerializer(source='driver', read_only=True)
    reviews = OrderReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set organization from request user
        validated_data['organization'] = self.context['request'].user.organisation
        return super().create(validated_data)




class DispatchOrdersSerializer(serializers.Serializer):
    """
    Serializer to handle dispatching of orders.

    This serializer is designed for dispatching orders to a specified driver. It
    validates the inputs, including the list of order IDs and the optional driver ID,
    ensuring the data provided is accurate and valid.

    :ivar order_ids: List of order IDs that are to be dispatched. This field is
        mandatory and cannot be empty.
    :type order_ids: List[UUID]
    :ivar driver_id: ID of the driver to whom the orders will be assigned. This
        field is optional and can be null.
    :type driver_id: UUID or None
    """
    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of order IDs to be dispatched"
    )
    driver_id = serializers.UUIDField(
        help_text="ID of the driver to whom the orders will be assigned",
        required=False,
        allow_null=True
    )

    def validate_driver_id(self, value):
        from users.models import Driver
        if value is None:
            return value
        try:
            Driver.objects.get(id=value).only('id')
        except Driver.DoesNotExist:
            raise serializers.ValidationError("Invalid driver")
        return value