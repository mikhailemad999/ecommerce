def cart_processor(request):
    """
    Context processor to add cart count to all templates
    """
    cart_items = request.session.get('cart_items', [])
    cart_count = sum(item.get('qty', 0) for item in cart_items)
    
    return {
        'cart_count': cart_count
    }
