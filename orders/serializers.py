# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem, ShippingAddress, ShippingCarrier, ShippingMethod, ShipmentTracking, TrackingCheckpoint
from products.serializers import ProductSerializer
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'name', 'isAdmin']
    
    def get_name(self, obj):
        name = obj.first_name
        if not name:
            name = obj.email
        return name
    
    def get_isAdmin(self, obj):
        return obj.is_staff


class ShippingCarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingCarrier
        fields = '__all__'


class ShippingMethodSerializer(serializers.ModelSerializer):
    carrier_detail = ShippingCarrierSerializer(source='carrier', read_only=True)

    class Meta:
        model = ShippingMethod
        fields = '__all__'


class TrackingCheckpointSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TrackingCheckpoint
        fields = ['id', 'status', 'status_display', 'title', 'location', 'description', 'timestamp']


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    checkpoints = TrackingCheckpointSerializer(many=True, read_only=True)
    progress_percent = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_current_status_display', read_only=True)

    class Meta:
        model = ShipmentTracking
        fields = '__all__'

    def get_progress_percent(self, obj):
        return obj.get_progress_percent()


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    orderItems = serializers.SerializerMethodField(read_only=True)
    shippingAddress = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    tracking = serializers.SerializerMethodField(read_only=True)
    shippingMethod = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
    
    def get_orderItems(self, obj):
        items = obj.orderitem_set.all()
        return OrderItemSerializer(items, many=True).data
    
    def get_shippingAddress(self, obj):
        try:
            return ShippingAddressSerializer(obj.shippingaddress, many=False).data
        except Exception:
            return None
    
    def get_user(self, obj):
        if not obj.user:
            return None
        return UserSerializer(obj.user, many=False).data

    def get_tracking(self, obj):
        try:
            return ShipmentTrackingSerializer(obj.tracking, many=False).data
        except Exception:
            return None

    def get_shippingMethod(self, obj):
        if obj.shipping_method:
            return ShippingMethodSerializer(obj.shipping_method, many=False).data
        return None
