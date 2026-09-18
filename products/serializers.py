# products/serializers.py
from rest_framework import serializers
from .models import Product, Review, Category, ProductSpecification, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'description', 'is_active', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'name', 'value', 'order']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField(read_only=True)
    specifications = serializers.SerializerMethodField(read_only=True)
    images = serializers.SerializerMethodField(read_only=True)
    category_detail = serializers.SerializerMethodField(read_only=True)
    on_sale = serializers.ReadOnlyField()
    discount_percent = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_reviews(self, obj):
        reviews = obj.review_set.all().order_by('-createdAt')
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data
    
    def get_specifications(self, obj):
        specs = obj.specifications.all()
        return ProductSpecificationSerializer(specs, many=True).data

    def get_images(self, obj):
        gallery = obj.images.all()
        return ProductImageSerializer(gallery, many=True).data

    def get_category_detail(self, obj):
        if obj.category_ref:
            return CategorySerializer(obj.category_ref, many=False).data
        return None

    def get_image(self, obj):
        if not obj.image:
            return '/static/images/placeholder.png'
        try:
            image_str = str(obj.image)
            if image_str.startswith('http://') or image_str.startswith('https://') or image_str.startswith('/'):
                return image_str
            if hasattr(obj.image, 'url'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
        except Exception:
            pass
        return '/static/images/placeholder.png'
