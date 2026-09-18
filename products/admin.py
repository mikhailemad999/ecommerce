from django.contrib import admin
from .models import Category, Product, ProductSpecification, ProductImage, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price', 'discount_price', 'countInStock', 'rating', 'is_featured', 'is_active')
    list_filter = ('is_featured', 'is_active', 'category', 'brand')
    search_fields = ('name', 'brand', 'description', 'sku', 'tags')
    inlines = [ProductSpecificationInline, ProductImageInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'name', 'rating', 'createdAt')
    list_filter = ('rating', 'createdAt')
    search_fields = ('name', 'comment', 'product__name', 'user__username')
