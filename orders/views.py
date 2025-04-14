# orders/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Order, OrderItem, ShippingAddress
from products.models import Product
from .serializers import OrderSerializer
from rest_framework import status
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addOrderItems(request):
    user = request.user
    data = request.data
    
    orderItems = data['orderItems']
    
    if len(orderItems) == 0:
        return Response({'detail': 'No Order Items'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Create order
        order = Order.objects.create(
            user=user,
            paymentMethod=data['paymentMethod'],
            taxPrice=data['taxPrice'],
            shippingPrice=data['shippingPrice'],
            totalPrice=data['totalPrice']
        )
        
        # Create shipping address
        shipping = ShippingAddress.objects.create(
            order=order,
            address=data['shippingAddress']['address'],
            city=data['shippingAddress']['city'],
            postalCode=data['shippingAddress']['postalCode'],
            country=data['shippingAddress']['country'],
            phone=data['shippingAddress'].get('phone', '')
        )
        
        # Create order items and set order to orderItem relationship
        for i in orderItems:
            product = Product.objects.get(id=i['product'])
            
            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                qty=i['qty'],
                price=i['price'],
                image=product.image.url,
            )
            
            # Update stock
            product.countInStock -= item.qty
            product.save()
        
        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getMyOrders(request):
    user = request.user
    orders = user.order_set.all()
    serializer = OrderSerializer(orders, many=True)
    return render(request, 'orders/my_orders.html', {'orders': serializer.data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderById(request, pk):
    user = request.user
    
    try:
        order = Order.objects.get(id=pk)
        
        if user.is_staff or order.user == user:
            serializer = OrderSerializer(order, many=False)
            return render(request, 'orders/order_detail.html', {'order': serializer.data})
        else:
            return Response({'detail': 'Not authorized to view this order'}, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'detail': 'Order does not exist'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateOrderToPaid(request, pk):
    order = Order.objects.get(id=pk)
    
    order.isPaid = True
    order.paidAt = datetime.now()
    order.save()
    
    return Response('Order was paid')

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateOrderToDelivered(request, pk):
    order = Order.objects.get(id=pk)
    
    order.isDelivered = True
    order.deliveredAt = datetime.now()
    order.save()
    
    return Response('Order was delivered')

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getAllOrders(request):
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)
    return render(request, 'orders/order_list.html', {'orders': serializer.data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def checkout(request):
    cart_items = request.session.get('cart_items', [])
    
    if not cart_items:
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    
    # Calculate prices
    items_price = request.session.get('items_price', 0)
    shipping_price = request.session.get('shipping_price', 0)
    tax_price = request.session.get('tax_price', 0)
    total_price = request.session.get('total_price', 0)
    
    context = {
        'cart_items': cart_items,
        'items_price': items_price,
        'shipping_price': shipping_price,
        'tax_price': tax_price,
        'total_price': total_price
    }
    
    return render(request, 'orders/create_order.html', context)
