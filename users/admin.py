from django.contrib import admin
from .models import Profile, CustomerAddress

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'loyalty_tier', 'phone_number', 'total_spent', 'created_at')
    list_filter = ('loyalty_tier', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')

@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'full_name', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('is_default', 'country', 'city')
    search_fields = ('full_name', 'street_address', 'city', 'user__username', 'phone')
