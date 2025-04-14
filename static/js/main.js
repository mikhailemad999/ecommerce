// Cart functionality
function updateCart() {
    const cartItems = JSON.parse(localStorage.getItem('cartItems') || '[]');
    const cartCount = cartItems.reduce((acc, item) => acc + item.qty, 0);
    
    // Update cart count in the navbar
    const cartElement = document.querySelector('.fa-shopping-cart');
    if (cartElement && cartCount > 0) {
        cartElement.insertAdjacentHTML('afterend', `<span class="cart-count">${cartCount}</span>`);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCart();
    
    // Add to cart functionality for product pages
    const addToCartBtn = document.getElementById('add-to-cart');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', function() {
            const productId = this.dataset.id;
            const productName = this.dataset.name;
            const productImage = this.dataset.image;
            const productPrice = parseFloat(this.dataset.price);
            const qty = parseInt(document.getElementById('qty').value);
            
            let cartItems = JSON.parse(localStorage.getItem('cartItems') || '[]');
            
            const existItem = cartItems.find(x => x.product === productId);
            
            if (existItem) {
                cartItems = cartItems.map(x => 
                    x.product === productId ? {...x, qty: x.qty + qty} : x
                );
            } else {
                cartItems.push({
                    product: productId,
                    name: productName,
                    image: productImage,
                    price: productPrice,
                    qty
                });
            }
            
            localStorage.setItem('cartItems', JSON.stringify(cartItems));
            updateCart();
            
            // Show success message
            const message = document.createElement('div');
            message.className = 'alert alert-success';
            message.textContent = 'Added to cart';
            document.querySelector('main').prepend(message);
            
            // Remove message after 3 seconds
            setTimeout(() => {
                message.remove();
            }, 3000);
        });
    }
});
