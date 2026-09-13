# orders/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Order, OrderItem, ShippingAddress
from products.models import Product
from .serializers import OrderSerializer
from rest_framework import status
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import json

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
    
    # Calculate prices
    items_price = sum(float(i.get('price', 0)) * int(i.get('qty', 1)) for i in order_items)
    shipping_price = 0.0 if items_price > 100 else 10.0
    tax_price = round(0.15 * items_price, 2)
    total_price = round(items_price + shipping_price + tax_price, 2)
    
    # Create order
    order = Order.objects.create(
        user=user,
        paymentMethod=data.get('paymentMethod', 'PayPal'),
        taxPrice=tax_price,
        shippingPrice=shipping_price,
        totalPrice=total_price,
        isPaid=False,
        isDelivered=False
    )
    
    # Create shipping address
    ShippingAddress.objects.create(
        order=order,
        address=shipping_info.get('address', 'N/A'),
        city=shipping_info.get('city', 'N/A'),
        postalCode=shipping_info.get('postalCode', 'N/A'),
        country=shipping_info.get('country', 'N/A'),
        phone=shipping_info.get('phone', ''),
        shippingPrice=shipping_price
    )
    
    # Create order items
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
    order.save()
    
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
    order.paymentMethod = 'Credit Card (Simulated)'
    order.save()
    messages.success(request, f'Payment of ${order.totalPrice} processed successfully via instant checkout test!')
    return redirect('user-order', pk=pk)


@api_view(['PUT', 'POST'])
@permission_classes([IsAdminUser])
def updateOrderToDelivered(request, pk):
    order = get_object_or_404(Order, id=pk)
    order.isDelivered = True
    order.deliveredAt = timezone.now()
    order.save()
    
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
    shipping_price = 0.0 if items_price > 100 else 10.0
    tax_price = round(0.15 * items_price, 2)
    total_price = round(items_price + shipping_price + tax_price, 2)
    
    # Save calculated values to session
    request.session['items_price'] = items_price
    request.session['shipping_price'] = shipping_price
    request.session['tax_price'] = tax_price
    request.session['total_price'] = total_price
    
    context = {
        'cart_items': cart_items,
        'items_price': f"{items_price:.2f}",
        'shipping_price': f"{shipping_price:.2f}",
        'tax_price': f"{tax_price:.2f}",
        'total_price': f"{total_price:.2f}",
        'user': request.user
    }
    return render(request, 'orders/create_order.html', context)
