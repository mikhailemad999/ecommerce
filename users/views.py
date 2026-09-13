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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from orders.models import Order
from orders.serializers import OrderSerializer
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_authenticated and user.is_staff

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
            return super().post(request, *args, **kwargs)
        else:
            # Handle standard form login
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            redirect_url = request.POST.get('redirect') or request.GET.get('redirect', '/')
            
            user = authenticate(request, username=username, password=password)
            if user is None and '@' in username:
                # If username was passed as email
                user_obj = User.objects.filter(email=username).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
                    
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect(redirect_url if redirect_url else '/')
            else:
                messages.error(request, 'Invalid email or password. Please try again.')
                return render(request, 'users/login.html', {'redirect': redirect_url})

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        redirect_url = request.GET.get('redirect', '/')
        return render(request, 'users/login.html', {'redirect': redirect_url})


@api_view(['POST', 'GET'])
def registerUser(request):
    if request.method == 'POST':
        is_json = request.content_type == 'application/json'
        data = request.data if is_json else request.POST
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')
        redirect_url = data.get('redirect') or request.GET.get('redirect', '/')
        
        if not name or not email or not password:
            msg = 'Please fill in all required fields'
            if is_json:
                return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
            messages.error(request, msg)
            return render(request, 'users/register.html', {'redirect': redirect_url})
            
        if password != confirm_password:
            msg = 'Passwords do not match'
            if is_json:
                return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
            messages.error(request, msg)
            return render(request, 'users/register.html', {'redirect': redirect_url})
            
        if len(password) < 6:
            msg = 'Password must be at least 6 characters'
            if is_json:
                return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
            messages.error(request, msg)
            return render(request, 'users/register.html', {'redirect': redirect_url})
        
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            msg = 'A user with this email address already exists'
            if is_json:
                return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
            messages.error(request, msg)
            return render(request, 'users/register.html', {'redirect': redirect_url})
        
        user = User.objects.create(
            first_name=name,
            username=email,
            email=email,
            password=make_password(password)
        )
        
        # Log user in immediately
        login(request, user)
        messages.success(request, f'Account created successfully! Welcome to the store, {name}.')
        
        if is_json:
            serializer = UserSerializerWithToken(user, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        return redirect(redirect_url if redirect_url else '/')
    else:
        if request.user.is_authenticated:
            return redirect('/')
        redirect_url = request.GET.get('redirect', '/')
        return render(request, 'users/register.html', {'redirect': redirect_url})


@login_required(login_url='/users/login/')
def updateUserProfile(request):
    user = request.user
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')
        
        if password and password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('users-profile')
            
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, 'This email is already in use by another account')
                return redirect('users-profile')
            user.email = email
            user.username = email
            
        if name:
            user.first_name = name
            
        if password:
            user.password = make_password(password)
            
        user.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('users-profile')
    else:
        serializer = UserSerializer(user, many=False)
        orders = user.order_set.all().order_by('-createdAt')
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


@user_passes_test(is_admin, login_url='/users/login/')
def getUsers(request):
    users = User.objects.all().order_by('id')
    serializer = UserSerializer(users, many=True)
    return render(request, 'users/user_list.html', {'users': serializer.data})


@user_passes_test(is_admin, login_url='/users/login/')
def getUserById(request, pk):
    user = get_object_or_404(User, id=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        is_admin_flag = 'isAdmin' in request.POST
        
        user.first_name = name
        user.email = email
        user.username = email
        user.is_staff = is_admin_flag
        user.save()
        messages.success(request, f'User {user.username} updated successfully')
        return redirect('users')
        
    serializer = UserSerializer(user, many=False)
    return render(request, 'users/user_edit.html', {'user': serializer.data})


@api_view(['PUT', 'POST'])
@permission_classes([IsAdminUser])
def updateUser(request, pk):
    user = get_object_or_404(User, id=pk)
    data = request.data if request.data else request.POST
    
    user.first_name = data.get('name', user.first_name)
    user.username = data.get('email', user.username)
    user.email = data.get('email', user.email)
    user.is_staff = data.get('isAdmin', user.is_staff)
    user.save()
    
    if request.content_type == 'application/json':
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
        
    messages.success(request, 'User updated successfully')
    return redirect('users')


@api_view(['DELETE', 'POST'])
@permission_classes([IsAdminUser])
def deleteUser(request, pk):
    user_to_delete = get_object_or_404(User, id=pk)
    username = user_to_delete.username
    
    if user_to_delete.id == request.user.id:
        if request.content_type == 'application/json':
            return Response({'detail': 'You cannot delete yourself'}, status=status.HTTP_400_BAD_REQUEST)
        messages.error(request, 'You cannot delete your own admin account')
        return redirect('users')
        
    user_to_delete.delete()
    
    if request.content_type == 'application/json':
        return Response({'detail': 'User deleted'})
        
    messages.success(request, f'User {username} deleted successfully')
    return redirect('users')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('/')
