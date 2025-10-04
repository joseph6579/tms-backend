class DriverTripsService:

    @staticmethod
    def trip_related_fields():
        return ['driver_profile', 'vehicle']

    @staticmethod
    def trip_fields():
        return [
            'id',
            'created_at',
            'updated_at',
            'status',
            'completed_time',
            'estimated_duration',
            'actual_duration',
            'planned_geometry',
            'actual_geometry',
            'notes',
            'distance',
            'start_point',
            'end_point',
            'driver_profile_id',
            'vehicle_id',
            'organisation_id',
        ]

    @staticmethod
    def trip_stop_fields():
        return [
            'id',
            'coordinates',
            'sequence',
            'stop_type',
            'trip_id',
            'order_id'
        ]

    @staticmethod
    def order_related_fields():
        return ['recipient', 'buyer', 'store', 'pickup', 'drop_off']


    @staticmethod
    def order_fields():
        return [
            'id',
            'reference_number',
            'description',
            'instructions',
            'recipient_id',
            'buyer_id',
            'store_id',
            'pickup_id',
            'drop_off_id'
        ]


driver_trips_svc = DriverTripsService()