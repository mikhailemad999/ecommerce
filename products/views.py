# products/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Product, Review
from .serializers import ProductSerializer
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib import messages

# products/views.py (update these functions)

# products/views.py (update the getProducts function)
@api_view(['GET'])
def getProducts(request):
    query = request.query_params.get('keyword', '')
    products = Product.objects.filter(name__icontains=query)
    
    page = request.query_params.get('page', 1)
    paginator = Paginator(products, 8)  # Show 8 products per page
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    if page == None:
        page = 1
    
    page = int(page)
    
    serializer = ProductSerializer(products, many=True, context={'request': request})
    
    context = {
        'products': serializer.data,
        'page': page,
        'pages': paginator.num_pages,
        'pages_range': range(1, paginator.num_pages + 1),
        'keyword': query
    }
    
    # Check if this is an API request or a template request
    if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return Response({'products': serializer.data, 'page': page, 'pages': paginator.num_pages})
    else:
        return render(request, 'products/product_list.html', context)


@api_view(['GET'])
def getProduct(request, pk):
    try:
        product = Product.objects.get(id=pk)
        serializer = ProductSerializer(product, many=False, context={'request': request})
        
        # Check if this is an API request or a template request
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return Response(serializer.data)
        else:
            return render(request, 'products/product_detail.html', {'product': serializer.data})
    except:
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            messages.error(request, 'Product not found')
            return redirect('products')




@api_view(['POST'])
@permission_classes([IsAdminUser])
def createProduct(request):
    user = request.user
    product = Product.objects.create(
        user=user,
        name='Sample Name',
        price=0,
        brand='Sample Brand',
        countInStock=0,
        category='Sample Category',
        description=''
    )
    serializer = ProductSerializer(product, many=False, context={'request': request})
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateProduct(request, pk):
    data = request.data
    product = Product.objects.get(id=pk)
    
    product.name = data['name']
    product.price = data['price']
    product.brand = data['brand']
    product.countInStock = data['countInStock']
    product.category = data['category']
    product.description = data['description']
    
    product.save()
    
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteProduct(request, pk):
    product = Product.objects.get(id=pk)
    product.delete()
    return Response('Product Deleted')

@api_view(['POST'])
def uploadImage(request):
    data = request.data
    
    product_id = data['product_id']
    product = Product.objects.get(id=product_id)
    
    product.image = request.FILES.get('image')
    product.save()
    
    serializer = ProductSerializer(product, many=False, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProductReview(request, pk):
    user = request.user
    product = Product.objects.get(id=pk)
    data = request.data
    
    # 1 - Review already exists
    alreadyExists = product.review_set.filter(user=user).exists()
    
    if alreadyExists:
        content = {'detail': 'Product already reviewed'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    
    # 2 - No Rating or 0
    elif data['rating'] == 0:
        content = {'detail': 'Please select a rating'}
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    
    # 3 - Create review
    else:
        review = Review.objects.create(
            user=user,
            product=product,
            name=user.first_name,
            rating=data['rating'],
            comment=data['comment'],
        )
        
        reviews = product.review_set.all()
        product.numReviews = len(reviews)
        
        total = 0
        for i in reviews:
            total += i.rating
        
        product.rating = total / len(reviews)
        product.save()
        
        return Response('Review Added')

# Add a view for the cart page
@api_view(['GET'])
def viewCart(request):
    return render(request, 'products/cart.html')


# Add a view to save cart data in session
@api_view(['POST'])
def saveCartToSession(request):
    data = request.data
    request.session['cart_items'] = data.get('cartItems', [])
    request.session['items_price'] = data.get('itemsPrice', 0)
    request.session['shipping_price'] = data.get('shippingPrice', 0)
    request.session['tax_price'] = data.get('taxPrice', 0)
    request.session['total_price'] = data.get('totalPrice', 0)
    
    return Response({'success': True})

