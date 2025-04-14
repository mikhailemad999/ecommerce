# products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getProducts, name='products'),
    path('create/', views.createProduct, name='product-create'),
    path('upload/', views.uploadImage, name='image-upload'),
    path('<str:pk>/reviews/', views.createProductReview, name='create-review'),
    path('<str:pk>/', views.getProduct, name='product'),
    path('update/<str:pk>/', views.updateProduct, name='product-update'),
    path('delete/<str:pk>/', views.deleteProduct, name='product-delete'),
    path('cart/save/', views.saveCartToSession, name='save-cart'),
]
