# Add to existing OrderViewSet class:

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """Broadcast orders to available drivers"""
        order_ids = request.data.get('order_ids', [])
        
        # Get orders
        orders = Order.objects.filter(
            id__in=order_ids,
            organization=request.user.organisation,
            status='pending',
            trip__isnull=True
        )

        if not orders:
            return Response(
                {'detail': 'No valid orders found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize broadcast service
        broadcast_service = BroadcastService()

        # Create batches
        batches = broadcast_service.create_batch_from_orders(list(orders))

        if not batches:
            return Response(
                {'detail': 'Could not create batches from orders'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Broadcast each batch
        results = []
        for batch in batches:
            success = broadcast_service.broadcast_batch(batch)
            results.append({
                'orders': [str(order.id) for order in batch['orders']],
                'broadcast_success': success
            })

        return Response(results)

    @action(detail=False, methods=['post'])
    def accept_batch(self, request):
        """Accept a broadcasted batch"""
        batch_id = request.data.get('batch_id')
        driver_id = request.data.get('driver_id')

        if not batch_id or not driver_id:
            return Response(
                {'detail': 'Batch ID and Driver ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        broadcast_service = BroadcastService()
        success = broadcast_service.handle_batch_acceptance(batch_id, driver_id)

        if success:
            return Response({'detail': 'Batch accepted successfully'})
        else:
            return Response(
                {'detail': 'Failed to accept batch'},
                status=status.HTTP_400_BAD_REQUEST
            )