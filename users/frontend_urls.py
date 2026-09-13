# users/frontend_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.MyTokenObtainPairView.as_view(), name='login'),
    path('register/', views.registerUser, name='register'),
    path('profile/', views.updateUserProfile, name='users-profile'),
    path('logout/', views.logout_view, name='logout'),
    path('manage/', views.getUsers, name='users'),
    path('manage/edit/<str:pk>/', views.getUserById, name='user-edit'),
    path('manage/delete/<str:pk>/', views.deleteUser, name='user-delete-front'),
]
