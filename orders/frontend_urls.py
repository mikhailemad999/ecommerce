# orders/frontend_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getAllOrders, name='orders'),
    path('myorders/', views.getMyOrders, name='myorders'),
    path('checkout/', views.checkout, name='checkout'),
    path('<str:pk>/', views.getOrderById, name='user-order'),
]
