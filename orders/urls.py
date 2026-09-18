# orders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.addOrderItems, name='orders-add'),
    path('myorders/', views.getMyOrders, name='api-myorders'),
    path('track/', views.trackOrderPublic, name='api-order-tracking'),
    path('<str:pk>/', views.getOrderById, name='api-order-detail'),
    path('<str:pk>/pay/', views.updateOrderToPaid, name='api-pay'),
    path('<str:pk>/deliver/', views.updateOrderToDelivered, name='api-deliver'),
    path('<str:pk>/checkpoint/', views.adminAddCheckpoint, name='api-checkpoint'),
    path('', views.getAllOrders, name='api-orders-list'),
]
