# products/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import Product, Review
from .serializers import ProductSerializer
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

def is_admin(user):
    return user.is_authenticated and user.is_staff

@api_view(['GET'])
def getProducts(request):
    query = request.GET.get('keyword', request.query_params.get('keyword', '')).strip()
    category = request.GET.get('category', request.query_params.get('category', '')).strip()
    sort = request.GET.get('sort', request.query_params.get('sort', '')).strip()
    
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query)
        )
    
    if category and category.lower() != 'all':
        products = products.filter(category__iexact=category)
    
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'rating':
        products = products.order_by('-rating', '-numReviews')
    elif sort == 'newest':
        products = products.order_by('-createdAt')
    else:
        products = products.order_by('-createdAt', '-id')
    
    # Get all distinct categories for filtering pills
    categories = list(Product.objects.exclude(category__isnull=True).exclude(category='').values_list('category', flat=True).distinct())
    
    page = request.GET.get('page', request.query_params.get('page', 1))
    paginator = Paginator(products, 8)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
        page = 1
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    
    serializer = ProductSerializer(page_obj, many=True, context={'request': request})
    
    if 'application/json' in request.META.get('HTTP_ACCEPT', '') and not request.path.startswith('/products/'):
        return Response({
            'products': serializer.data,
            'page': int(page),
            'pages': paginator.num_pages,
            'total': paginator.count
        })
    
    context = {
        'products': serializer.data,
        'page': int(page),
        'pages': paginator.num_pages,
        'pages_range': range(1, paginator.num_pages + 1),
        'keyword': query,
        'selected_category': category,
        'categories': categories,
        'sort': sort,
        'total_count': paginator.count
    }
    return render(request, 'products/product_list.html', context)


@api_view(['GET'])
def getProduct(request, pk):
    try:
        product = Product.objects.get(id=pk)
        serializer = ProductSerializer(product, many=False, context={'request': request})
        
        if 'application/json' in request.META.get('HTTP_ACCEPT', '') and not request.path.startswith('/products/'):
            return Response(serializer.data)
        
        # Related products
        related_qs = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        if not related_qs.exists():
            related_qs = Product.objects.exclude(id=product.id)[:4]
        related_serializer = ProductSerializer(related_qs, many=True, context={'request': request})
        
        return render(request, 'products/product_detail.html', {
            'product': serializer.data,
            'related_products': related_serializer.data
        })
    except Product.DoesNotExist:
        if 'application/json' in request.META.get('HTTP_ACCEPT', '') and not request.path.startswith('/products/'):
            return Response({'detail': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        messages.error(request, 'Product not found')
        return redirect('products')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProductReview(request, pk):
    user = request.user
    product = get_object_or_404(Product, id=pk)
    
    data = request.data if request.data else request.POST
    
    # 1 - Review already exists
    alreadyExists = product.review_set.filter(user=user).exists()
    if alreadyExists:
        if request.content_type == 'application/json':
            return Response({'detail': 'You have already reviewed this product'}, status=status.HTTP_400_BAD_REQUEST)
        messages.warning(request, 'You have already reviewed this product')
        return redirect('product', pk=pk)
    
    # 2 - Validate Rating
    try:
        rating_val = int(data.get('rating', 0))
    except (ValueError, TypeError):
        rating_val = 0
        
    if rating_val <= 0 or rating_val > 5:
        if request.content_type == 'application/json':
            return Response({'detail': 'Please select a rating between 1 and 5'}, status=status.HTTP_400_BAD_REQUEST)
        messages.error(request, 'Please select a valid rating')
        return redirect('product', pk=pk)
    
    # 3 - Create review
    comment = data.get('comment', '').strip()
    Review.objects.create(
        user=user,
        product=product,
        name=user.first_name if user.first_name else user.username,
        rating=rating_val,
        comment=comment,
    )
    
    # Recalculate product rating
    reviews = product.review_set.all()
    product.numReviews = reviews.count()
    total = sum(r.rating for r in reviews)
    product.rating = round(total / product.numReviews, 2)
    product.save()
    
    if request.content_type == 'application/json':
        return Response({'detail': 'Review added successfully'}, status=status.HTTP_201_CREATED)
    
    messages.success(request, 'Thank you! Your review has been published.')
    return redirect('product', pk=pk)


# Cart Views
def viewCart(request):
    return render(request, 'products/cart.html')


@api_view(['POST'])
def saveCartToSession(request):
    data = request.data
    cart_items = data.get('cartItems', [])
    
    request.session['cart_items'] = cart_items
    request.session['items_price'] = data.get('itemsPrice', 0)
    request.session['shipping_price'] = data.get('shippingPrice', 0)
    request.session['tax_price'] = data.get('taxPrice', 0)
    request.session['total_price'] = data.get('totalPrice', 0)
    request.session.modified = True
    
    return Response({'success': True, 'count': sum(i.get('qty', 0) for i in cart_items)})


# Admin Web Management Views
@user_passes_test(is_admin, login_url='/users/login/')
def adminProductList(request):
    query = request.GET.get('keyword', '').strip()
    products = Product.objects.all().order_by('-createdAt', '-id')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__icontains=query)
        )
    
    paginator = Paginator(products, 10)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except Exception:
        page_obj = paginator.page(1)
        
    return render(request, 'products/admin_product_list.html', {
        'products': page_obj,
        'keyword': query
    })


@user_passes_test(is_admin, login_url='/users/login/')
def adminProductCreate(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', 0)
        brand = request.POST.get('brand', '').strip()
        category = request.POST.get('category', '').strip()
        countInStock = request.POST.get('countInStock', 0)
        description = request.POST.get('description', '').strip()
        image = request.FILES.get('image')
        image_url = request.POST.get('image_url', '').strip()
        
        product = Product.objects.create(
            user=request.user,
            name=name or 'New Product',
            price=float(price or 0),
            brand=brand or 'General',
            category=category or 'Electronics',
            countInStock=int(countInStock or 0),
            description=description or '',
            rating=5.0,
            numReviews=0
        )
        
        if image:
            product.image = image
            product.save()
        elif image_url:
            product.image = image_url
            product.save()
        else:
            product.image = '/static/images/placeholder.png'
            product.save()
            
        messages.success(request, f'Product "{product.name}" created successfully!')
        return redirect('admin-products')
        
    return render(request, 'products/admin_product_form.html', {
        'title': 'Create Product',
        'is_edit': False
    })


@user_passes_test(is_admin, login_url='/users/login/')
def adminProductEdit(request, pk):
    product = get_object_or_404(Product, id=pk)
    
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.price = float(request.POST.get('price', product.price))
        product.brand = request.POST.get('brand', product.brand).strip()
        product.category = request.POST.get('category', product.category).strip()
        product.countInStock = int(request.POST.get('countInStock', product.countInStock))
        product.description = request.POST.get('description', product.description).strip()
        
        image = request.FILES.get('image')
        image_url = request.POST.get('image_url', '').strip()
        if image:
            product.image = image
        elif image_url:
            product.image = image_url
            
        product.save()
        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('admin-products')
        
    return render(request, 'products/admin_product_form.html', {
        'title': 'Edit Product',
        'product': product,
        'is_edit': True
    })


@user_passes_test(is_admin, login_url='/users/login/')
def adminProductDelete(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=pk)
        prod_name = product.name
        product.delete()
        messages.success(request, f'Product "{prod_name}" has been deleted.')
    return redirect('admin-products')


# DRF API Endpoints
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
    product = get_object_or_404(Product, id=pk)
    
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.brand = data.get('brand', product.brand)
    product.countInStock = data.get('countInStock', product.countInStock)
    product.category = data.get('category', product.category)
    product.description = data.get('description', product.description)
    
    product.save()
    serializer = ProductSerializer(product, many=False, context={'request': request})
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteProduct(request, pk):
    product = get_object_or_404(Product, id=pk)
    product.delete()
    return Response({'detail': 'Product Deleted'})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def uploadImage(request):
    product_id = request.data.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    if 'image' in request.FILES:
        product.image = request.FILES['image']
        product.save()
    serializer = ProductSerializer(product, many=False, context={'request': request})
    return Response(serializer.data)
