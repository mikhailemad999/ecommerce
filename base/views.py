# base/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone

def home(request):
    return render(request, 'home.html')

def health_check(request):
    """
    Production health check endpoint for container orchestrators,
    Kubernetes readiness/liveness probes, and AWS/GCP load balancers.
    """
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse({
        'status': 'healthy' if db_ok else 'unhealthy',
        'database': 'connected' if db_ok else 'disconnected',
        'timestamp': timezone.now().isoformat(),
        'service': 'LuxeCommerce Production API'
    }, status=status_code)
