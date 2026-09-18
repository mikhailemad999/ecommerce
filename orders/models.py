# orders/models.py
from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.utils import timezone
import uuid

class ShippingCarrier(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    tracking_url_template = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. https://www.fedex.com/fedextrack/?trknbr={}")
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Shipping Carrier'
        verbose_name_plural = 'Shipping Carriers'
        ordering = ['name']

    def __str__(self):
        return self.name


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.SET_NULL, null=True, blank=True, related_name='methods')
    description = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.DecimalField(max_digits=7, decimal_places=2, default=10.00)
    estimated_days_min = models.IntegerField(default=2)
    estimated_days_max = models.IntegerField(default=5)
    free_shipping_threshold = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, default=100.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Shipping Method'
        verbose_name_plural = 'Shipping Methods'
        ordering = ['base_price']

    def __str__(self):
        return f"{self.name} (${self.base_price}) - {self.estimated_days_min}-{self.estimated_days_max} days"


class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Payment Confirmed / Processing'),
        ('SHIPPED', 'Dispatched / In Transit'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    paymentMethod = models.CharField(max_length=200, null=True, blank=True)
    taxPrice = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    shippingPrice = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    totalPrice = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    isPaid = models.BooleanField(default=False)
    paidAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    isDelivered = models.BooleanField(default=False)
    deliveredAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-createdAt']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username if self.user else 'Guest'} (${self.totalPrice})"


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    qty = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    image = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return str(self.name)


class ShippingAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    postalCode = models.CharField(max_length=200, null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    shippingPrice = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.address}, {self.city}, {self.country}"


class ShipmentTracking(models.Model):
    TRACKING_STATUSES = [
        ('ORDER_PLACED', 'Order Placed'),
        ('PROCESSING', 'Processing & Packaging'),
        ('DISPATCHED', 'Dispatched from Warehouse'),
        ('IN_TRANSIT', 'In Transit with Carrier'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('EXCEPTION', 'Delivery Exception / Delay'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='tracking')
    tracking_number = models.CharField(max_length=100, unique=True)
    carrier = models.ForeignKey(ShippingCarrier, on_delete=models.SET_NULL, null=True, blank=True)
    carrier_name = models.CharField(max_length=100, default='LuxeCommerce Express')
    current_status = models.CharField(max_length=40, choices=TRACKING_STATUSES, default='ORDER_PLACED')
    origin_facility = models.CharField(max_length=200, default='Central Logistics Hub, CA, USA')
    destination = models.CharField(max_length=200, blank=True, null=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    signature_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Tracking {self.tracking_number} (Order #{self.order_id}) - {self.get_current_status_display()}"

    def get_progress_percent(self):
        mapping = {
            'ORDER_PLACED': 15,
            'PROCESSING': 35,
            'DISPATCHED': 55,
            'IN_TRANSIT': 75,
            'OUT_FOR_DELIVERY': 90,
            'DELIVERED': 100,
            'EXCEPTION': 50,
        }
        return mapping.get(self.current_status, 15)


class TrackingCheckpoint(models.Model):
    tracking = models.ForeignKey(ShipmentTracking, on_delete=models.CASCADE, related_name='checkpoints')
    status = models.CharField(max_length=40, choices=ShipmentTracking.TRACKING_STATUSES)
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.title} @ {self.location} ({self.timestamp.strftime('%b %d, %H:%M')})"
