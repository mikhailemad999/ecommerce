# orders/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Order, OrderItem, ShippingAddress, ShippingCarrier, ShippingMethod, ShipmentTracking, TrackingCheckpoint
from products.models import Product
from users.models import CustomerAddress
from .serializers import OrderSerializer, ShipmentTrackingSerializer, ShippingMethodSerializer
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import random

def is_admin(user):
    return user.is_authenticated and user.is_staff

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addOrderItems(request):
    user = request.user
    data = request.data
    
    order_items = data.get('orderItems', [])
    if not order_items or len(order_items) == 0:
        return Response({'detail': 'No items in order'}, status=status.HTTP_400_BAD_REQUEST)
    
    shipping_info = data.get('shippingAddress', {})
    shipping_method_id = data.get('shippingMethodId')
    
    # Calculate prices
    items_price = sum(float(i.get('price', 0)) * int(i.get('qty', 1)) for i in order_items)
    
    # Resolve shipping method
    shipping_method = None
    if shipping_method_id:
        try:
            shipping_method = ShippingMethod.objects.get(id=shipping_method_id, is_active=True)
        except (ShippingMethod.DoesNotExist, ValueError):
            shipping_method = None

    if not shipping_method:
        shipping_method = ShippingMethod.objects.filter(is_active=True).first()

    if shipping_method:
        if shipping_method.free_shipping_threshold and items_price >= float(shipping_method.free_shipping_threshold):
            shipping_price = 0.0
        else:
            shipping_price = float(shipping_method.base_price)
    else:
        shipping_price = 0.0 if items_price > 100 else 10.0

    tax_price = round(0.15 * items_price, 2)
    total_price = round(items_price + shipping_price + tax_price, 2)
    
    # Generate unique tracking code
    rand_code = random.randint(10000, 99999)
    tracking_code = f"LX-{timezone.now().strftime('%y%m')}-{rand_code}-US"

    # Create order
    order = Order.objects.create(
        user=user,
        shipping_method=shipping_method,
        status='PENDING',
        paymentMethod=data.get('paymentMethod', 'Credit Card'),
        taxPrice=tax_price,
        shippingPrice=shipping_price,
        totalPrice=total_price,
        tracking_code=tracking_code,
        isPaid=False,
        isDelivered=False,
        notes=data.get('notes', '')
    )
    
    # Create shipping address
    ShippingAddress.objects.create(
        order=order,
        address=shipping_info.get('address', 'N/A'),
        city=shipping_info.get('city', 'N/A'),
        postalCode=shipping_info.get('postalCode', 'N/A'),
        country=shipping_info.get('country', 'United States'),
        phone=shipping_info.get('phone', ''),
        shippingPrice=shipping_price
    )
    
    # If user selected to save address to address book
    if data.get('saveAddress') and shipping_info.get('address'):
        CustomerAddress.objects.get_or_create(
            user=user,
            street_address=shipping_info.get('address'),
            city=shipping_info.get('city'),
            defaults={
                'title': data.get('addressTitle', 'Home'),
                'full_name': shipping_info.get('fullName', user.first_name or user.username),
                'phone': shipping_info.get('phone', ''),
                'postal_code': shipping_info.get('postalCode', ''),
                'country': shipping_info.get('country', 'United States'),
                'is_default': False
            }
        )

    # Create order items and adjust stock
    for item in order_items:
        prod_id = item.get('product')
        qty = int(item.get('qty', 1))
        
        try:
            product = Product.objects.get(id=prod_id)
            OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                qty=qty,
                price=product.price,
                image=str(product.image) if product.image else '/static/images/placeholder.png'
            )
            # Reduce inventory
            if product.countInStock >= qty:
                product.countInStock -= qty
            else:
                product.countInStock = 0
            product.save()
        except Product.DoesNotExist:
            continue

    # Initialize ShipmentTracking record
    est_days = shipping_method.estimated_days_max if shipping_method else 4
    carrier_obj = shipping_method.carrier if shipping_method else None
    carrier_title = carrier_obj.name if carrier_obj else 'LuxeCommerce Logistics'
    
    tracking = ShipmentTracking.objects.create(
        order=order,
        tracking_number=tracking_code,
        carrier=carrier_obj,
        carrier_name=carrier_title,
        current_status='ORDER_PLACED',
        origin_facility='LuxeCommerce Central Hub, San Jose CA',
        destination=f"{shipping_info.get('city', 'Destination City')}, {shipping_info.get('country', 'US')}",
        estimated_delivery=timezone.now() + timedelta(days=est_days),
        signature_required=total_price > 500
    )

    TrackingCheckpoint.objects.create(
        tracking=tracking,
        status='ORDER_PLACED',
        title='Order Received & Payment Processing',
        location='LuxeCommerce Hub, San Jose CA',
        description='Order confirmed and queued for white-glove security packaging and barcode tagging.',
        timestamp=timezone.now()
    )
            
    # Clear session cart
    request.session['cart_items'] = []
    request.session['items_price'] = 0
    request.session['shipping_price'] = 0
    request.session['tax_price'] = 0
    request.session['total_price'] = 0
    request.session.modified = True
    
    serializer = OrderSerializer(order, many=False)
    resp_data = serializer.data
    resp_data['_id'] = order.id
    resp_data['id'] = order.id
    return Response(resp_data, status=status.HTTP_201_CREATED)


@login_required(login_url='/users/login/?redirect=/orders/myorders/')
def getMyOrders(request):
    user = request.user
    orders = user.order_set.all().order_by('-createdAt')
    serializer = OrderSerializer(orders, many=True)
    return render(request, 'orders/my_orders.html', {'orders': serializer.data})


@login_required(login_url='/users/login/')
def getOrderById(request, pk):
    user = request.user
    order = get_object_or_404(Order, id=pk)
    
    if not (user.is_staff or order.user == user):
        messages.error(request, 'Not authorized to view this order')
        return redirect('myorders')
        
    serializer = OrderSerializer(order, many=False)
    
    if 'application/json' in request.META.get('HTTP_ACCEPT', '') and not request.path.startswith('/orders/'):
        return Response(serializer.data)
        
    return render(request, 'orders/order_detail.html', {'order': serializer.data})


@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated])
def updateOrderToPaid(request, pk):
    order = get_object_or_404(Order, id=pk)
    
    if not (request.user.is_staff or order.user == request.user):
        return Response({'detail': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
    order.isPaid = True
    order.paidAt = timezone.now()
    order.status = 'PAID'
    order.save()

    # Update tracking checkpoint
    if hasattr(order, 'tracking'):
        tracking = order.tracking
        tracking.current_status = 'PROCESSING'
        tracking.save()
        TrackingCheckpoint.objects.create(
            tracking=tracking,
            status='PROCESSING',
            title='Payment Verified & Parcel In Processing',
            location='Central Fulfillment Hub, CA',
            description='Payment authorized. Warehouse team is inspecting items and printing shipping labels.',
            timestamp=timezone.now()
        )
    
    if request.content_type == 'application/json' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return Response({'detail': 'Order was paid', 'isPaid': True, 'paidAt': str(order.paidAt)})
        
    messages.success(request, f'Order #{order.id} payment confirmed successfully!')
    return redirect('user-order', pk=pk)


@login_required(login_url='/users/login/')
def testCardPayment(request, pk):
    order = get_object_or_404(Order, id=pk)
    if not (request.user.is_staff or order.user == request.user):
        messages.error(request, 'Not authorized')
        return redirect('myorders')
        
    order.isPaid = True
    order.paidAt = timezone.now()
    order.status = 'PAID'
    order.paymentMethod = 'Credit Card (Simulated)'
    order.save()

    # Update tracking
    if hasattr(order, 'tracking'):
        tracking = order.tracking
        tracking.current_status = 'PROCESSING'
        tracking.save()
        TrackingCheckpoint.objects.create(
            tracking=tracking,
            status='PROCESSING',
            title='Instant Payment Authorized & Packaged',
            location='Central Fulfillment Hub, CA',
            description='1-Click sandbox transaction approved. Parcel moving to carrier transfer bay.',
            timestamp=timezone.now()
        )

    messages.success(request, f'Payment of ${order.totalPrice} processed successfully via instant checkout test!')
    return redirect('user-order', pk=pk)


@api_view(['PUT', 'POST'])
@permission_classes([IsAdminUser])
def updateOrderToDelivered(request, pk):
    order = get_object_or_404(Order, id=pk)
    order.isDelivered = True
    order.deliveredAt = timezone.now()
    order.status = 'DELIVERED'
    order.save()

    # Update tracking
    if hasattr(order, 'tracking'):
        tracking = order.tracking
        tracking.current_status = 'DELIVERED'
        tracking.actual_delivery = timezone.now()
        tracking.save()
        TrackingCheckpoint.objects.create(
            tracking=tracking,
            status='DELIVERED',
            title='Delivered to Recipient',
            location=order.shippingaddress.city if hasattr(order, 'shippingaddress') and order.shippingaddress else 'Destination',
            description='Delivered and handed over in secure condition.',
            timestamp=timezone.now()
        )
    
    if request.content_type == 'application/json' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return Response({'detail': 'Order marked as delivered', 'isDelivered': True, 'deliveredAt': str(order.deliveredAt)})
        
    messages.success(request, f'Order #{order.id} marked as delivered!')
    return redirect('user-order', pk=pk)


@user_passes_test(is_admin, login_url='/users/login/')
def getAllOrders(request):
    orders = Order.objects.all().order_by('-createdAt')
    filter_status = request.GET.get('status', 'all')
    
    if filter_status == 'paid':
        orders = orders.filter(isPaid=True)
    elif filter_status == 'unpaid':
        orders = orders.filter(isPaid=False)
    elif filter_status == 'delivered':
        orders = orders.filter(isDelivered=True)
    elif filter_status == 'pending_delivery':
        orders = orders.filter(isPaid=True, isDelivered=False)
        
    serializer = OrderSerializer(orders, many=True)
    return render(request, 'orders/order_list.html', {
        'orders': serializer.data,
        'filter_status': filter_status,
        'total_orders': Order.objects.count()
    })


@login_required(login_url='/users/login/?redirect=/orders/checkout/')
def checkout(request):
    cart_items = request.session.get('cart_items', [])
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty. Please add items before checking out.')
        return redirect('cart')
    
    items_price = sum(float(item.get('price', 0)) * int(item.get('qty', 1)) for item in cart_items)
    
    # Available shipping methods
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    default_shipping_method = shipping_methods.first()
    
    if default_shipping_method:
        if default_shipping_method.free_shipping_threshold and items_price >= float(default_shipping_method.free_shipping_threshold):
            shipping_price = 0.0
        else:
            shipping_price = float(default_shipping_method.base_price)
    else:
        shipping_price = 0.0 if items_price > 100 else 10.0

    tax_price = round(0.15 * items_price, 2)
    total_price = round(items_price + shipping_price + tax_price, 2)
    
    # Save calculated values to session
    request.session['items_price'] = items_price
    request.session['shipping_price'] = shipping_price
    request.session['tax_price'] = tax_price
    request.session['total_price'] = total_price
    
    # Customer saved addresses
    saved_addresses = CustomerAddress.objects.filter(user=request.user)
    
    context = {
        'cart_items': cart_items,
        'items_price': f"{items_price:.2f}",
        'shipping_price': f"{shipping_price:.2f}",
        'tax_price': f"{tax_price:.2f}",
        'total_price': f"{total_price:.2f}",
        'user': request.user,
        'shipping_methods': shipping_methods,
        'saved_addresses': saved_addresses
    }
    return render(request, 'orders/create_order.html', context)


def trackOrderPublic(request):
    """
    Public and customer order tracking portal.
    Users can look up tracking by tracking number or order ID.
    """
    query = request.GET.get('tracking_number', '').strip()
    tracking_record = None
    not_found = False

    if query:
        # Search by tracking number or order ID
        tracking_record = ShipmentTracking.objects.filter(tracking_number__iexact=query).first()
        if not tracking_record and query.isdigit():
            tracking_record = ShipmentTracking.objects.filter(order__id=int(query)).first()
        if not tracking_record:
            not_found = True

    if 'application/json' in request.META.get('HTTP_ACCEPT', '') and not request.path.startswith('/orders/track/'):
        if tracking_record:
            return Response(ShipmentTrackingSerializer(tracking_record).data)
        elif not_found:
            return Response({'detail': 'Tracking record not found'}, status=status.HTTP_404_NOT_FOUND)

    context = {
        'query': query,
        'tracking': tracking_record,
        'not_found': not_found
    }
    return render(request, 'orders/order_tracking.html', context)


@user_passes_test(is_admin, login_url='/users/login/')
def adminAddCheckpoint(request, pk):
    """
    Staff control to append a real-time scanning checkpoint to an order's shipment.
    """
    order = get_object_or_404(Order, id=pk)
    if not hasattr(order, 'tracking'):
        messages.error(request, 'No tracking record found for this order.')
        return redirect('user-order', pk=pk)

    if request.method == 'POST':
        checkpoint_status = request.POST.get('status', 'IN_TRANSIT')
        title = request.POST.get('title', 'Carrier Scan')
        location = request.POST.get('location', 'Sort Facility')
        description = request.POST.get('description', '')

        tracking = order.tracking
        tracking.current_status = checkpoint_status
        if checkpoint_status == 'DELIVERED':
            order.isDelivered = True
            order.deliveredAt = timezone.now()
            order.status = 'DELIVERED'
            order.save()
            tracking.actual_delivery = timezone.now()
        tracking.save()

        TrackingCheckpoint.objects.create(
            tracking=tracking,
            status=checkpoint_status,
            title=title,
            location=location,
            description=description,
            timestamp=timezone.now()
        )
        messages.success(request, f'New tracking checkpoint "{title}" logged successfully!')

    return redirect('user-order', pk=pk)
