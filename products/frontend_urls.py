# products/frontend_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getProducts, name='products'),
    path('cart/', views.viewCart, name='cart'),
    path('<str:pk>/', views.getProduct, name='product'),
]
