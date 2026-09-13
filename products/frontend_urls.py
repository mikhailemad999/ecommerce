# products/frontend_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getProducts, name='products'),
    path('cart/', views.viewCart, name='cart'),
    path('admin-manage/', views.adminProductList, name='admin-products'),
    path('admin-manage/create/', views.adminProductCreate, name='admin-product-create'),
    path('admin-manage/edit/<str:pk>/', views.adminProductEdit, name='admin-product-edit'),
    path('admin-manage/delete/<str:pk>/', views.adminProductDelete, name='admin-product-delete'),
    path('<str:pk>/', views.getProduct, name='product'),
]
