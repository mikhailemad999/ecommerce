from django.contrib import admin
from .models import ShippingCarrier, ShippingMethod, Order, OrderItem, ShippingAddress, ShipmentTracking, TrackingCheckpoint

@admin.register(ShippingCarrier)
class ShippingCarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_phone', 'website', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'carrier', 'base_price', 'estimated_days_min', 'estimated_days_max', 'is_active')
    list_filter = ('is_active', 'carrier')
    search_fields = ('name', 'code')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'name', 'qty', 'price', 'image')

class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 0

class TrackingCheckpointInline(admin.TabularInline):
    model = TrackingCheckpoint
    extra = 1

@admin.register(ShipmentTracking)
class ShipmentTrackingAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order', 'carrier_name', 'current_status', 'estimated_delivery', 'actual_delivery')
    list_filter = ('current_status', 'carrier')
    search_fields = ('tracking_number', 'order__id', 'carrier_name', 'destination')
    inlines = [TrackingCheckpointInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'totalPrice', 'isPaid', 'paidAt', 'isDelivered', 'deliveredAt', 'tracking_code', 'createdAt')
    list_filter = ('status', 'isPaid', 'isDelivered', 'createdAt')
    search_fields = ('id', 'user__username', 'user__email', 'tracking_code')
    inlines = [OrderItemInline, ShippingAddressInline]

@admin.register(TrackingCheckpoint)
class TrackingCheckpointAdmin(admin.ModelAdmin):
    list_display = ('tracking', 'status', 'title', 'location', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('title', 'location', 'tracking__tracking_number')
