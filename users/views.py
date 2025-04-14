# users/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserSerializer, UserSerializerWithToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import make_password
from rest_framework import status
from django.shortcuts import render, redirect
from django.contrib import messages
from orders.models import Order
from orders.serializers import OrderSerializer
from django.contrib.auth import authenticate, login

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerWithToken(self.user).data
        for k, v in serializer.items():
            data[k] = v
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        if request.content_type == 'application/json':
            # Handle API JSON login
            return super().post(request, *args, **kwargs)
        else:
            # Handle form login
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                redirect_url = request.GET.get('redirect', '/')
                return redirect(redirect_url)
            else:
                messages.error(request, 'Invalid email or password')
                return render(request, 'users/login.html')

    def get(self, request):
        return render(request, 'users/login.html')

@api_view(['POST', 'GET'])
def registerUser(request):
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = request.data
        else:
            data = request.POST
        
        if data['password'] != data['confirmPassword']:
            messages.error(request, 'Passwords do not match')
            return render(request, 'users/register.html')
        
        try:
            user = User.objects.create(
                first_name=data['name'],
                username=data['email'],
                email=data['email'],
                password=make_password(data['password'])
            )
            
            redirect_url = data.get('redirect', '/')
            return redirect(redirect_url)
        
# users/views.py (continued)
        except:
            messages.error(request, 'User with this email already exists')
            return render(request, 'users/register.html')
    else:
        return render(request, 'users/register.html')

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def updateUserProfile(request):
    user = request.user
    
    if request.method == 'POST':
        data = request.data
        
        if data['password'] != '' and data['password'] != data['confirmPassword']:
            messages.error(request, 'Passwords do not match')
            return redirect('user-profile')
        
        user.first_name = data['name']
        user.username = data['email']
        user.email = data['email']
        
        if data['password'] != '':
            user.password = make_password(data['password'])
        
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('user-profile')
    else:
        serializer = UserSerializer(user, many=False)
        orders = user.order_set.all()
        orders_serializer = OrderSerializer(orders, many=True)
        
        return render(request, 'users/profile.html', {
            'user': serializer.data,
            'orders': orders_serializer.data
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return render(request, 'users/user_list.html', {'users': serializer.data})

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUserById(request, pk):
    user = User.objects.get(id=pk)
    serializer = UserSerializer(user, many=False)
    return render(request, 'users/user_edit.html', {'user': serializer.data})

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateUser(request, pk):
    user = User.objects.get(id=pk)
    
    data = request.data
    user.first_name = data['name']
    user.username = data['email']
    user.email = data['email']
    user.is_staff = data.get('isAdmin', False)
    
    user.save()
    
    messages.success(request, 'User updated successfully')
    return redirect('users')

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteUser(request, pk):
    userForDeletion = User.objects.get(id=pk)
    userForDeletion.delete()
    messages.success(request, 'User deleted successfully')
    return redirect('users')

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('/')
