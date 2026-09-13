/**
 * Neo-Luxe Commerce Core Client Logic
 */

// Universal CSRF Cookie getter
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Update Cart Count Badge in Header
function syncCartBadge() {
    const badge = document.getElementById('navbar-cart-count');
    if (!badge) return;
    
    try {
        const cartItems = JSON.parse(localStorage.getItem('cartItems') || '[]');
        const count = cartItems.reduce((acc, item) => acc + (parseInt(item.qty) || 1), 0);
        
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.textContent = '0';
            badge.style.display = 'none';
        }
    } catch (e) {
        console.error('Error reading cart:', e);
    }
}

// Add Item to Cart and Sync to Server Session
async function addProductToCart(productData, qty = 1, showToast = true) {
    try {
        let cartItems = JSON.parse(localStorage.getItem('cartItems') || '[]');
        const existingIndex = cartItems.findIndex(x => String(x.product) === String(productData.id || productData.product));
        
        const itemObj = {
            product: String(productData.id || productData.product),
            name: productData.name,
            image: productData.image,
            price: parseFloat(productData.price),
            countInStock: parseInt(productData.countInStock || 10),
            qty: parseInt(qty)
        };
        
        if (existingIndex > -1) {
            cartItems[existingIndex].qty = Math.min(
                cartItems[existingIndex].qty + qty,
                cartItems[existingIndex].countInStock
            );
        } else {
            cartItems.push(itemObj);
        }
        
        localStorage.setItem('cartItems', JSON.stringify(cartItems));
        syncCartBadge();
        
        // Sync with Django session in background
        await syncSessionCart(cartItems);
        
        if (showToast) {
            showNotification(`Added "${productData.name}" to your cart!`, 'success');
        }
        return true;
    } catch (err) {
        console.error('Add to cart failed:', err);
        return false;
    }
}

// Sync cart to backend session
async function syncSessionCart(cartItems) {
    const csrftoken = getCookie('csrftoken');
    const itemsPrice = cartItems.reduce((acc, item) => acc + (parseFloat(item.price) * parseInt(item.qty)), 0);
    const shippingPrice = itemsPrice > 100 || itemsPrice === 0 ? 0 : 10;
    const taxPrice = Math.round(itemsPrice * 0.15 * 100) / 100;
    const totalPrice = Math.round((itemsPrice + shippingPrice + taxPrice) * 100) / 100;
    
    try {
        await fetch('/api/products/cart/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                cartItems: cartItems,
                itemsPrice: itemsPrice.toFixed(2),
                shippingPrice: shippingPrice.toFixed(2),
                taxPrice: taxPrice.toFixed(2),
                totalPrice: totalPrice.toFixed(2)
            })
        });
    } catch (e) {
        console.warn('Session sync warning:', e);
    }
}

// Modern Toast Notification
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} alert-dismissible fade show position-fixed`;
    toast.style.top = '80px';
    toast.style.right = '20px';
    toast.style.zIndex = '99999';
    toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
    toast.style.borderRadius = '12px';
    toast.style.maxWidth = '360px';
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="fas ${type === 'success' ? 'fa-check-circle text-success' : 'fa-info-circle'}"></i>
            <div>${message}</div>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

document.addEventListener('DOMContentLoaded', () => {
    syncCartBadge();
    
    // Auto dismiss existing alerts after 4s
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }, 4000);
    });
});
