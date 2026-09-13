# orders/frontend_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.getAllOrders, name='orders'),
    path('myorders/', views.getMyOrders, name='myorders'),
    path('checkout/', views.checkout, name='checkout'),
    path('<str:pk>/', views.getOrderById, name='user-order'),
    path('<str:pk>/test-pay/', views.testCardPayment, name='order-test-pay'),
    path('<str:pk>/deliver/', views.updateOrderToDelivered, name='order-deliver'),
]
