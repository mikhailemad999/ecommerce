# ecommerce/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    
    # Frontend URLs
    path('', RedirectView.as_view(url='/products/'), name='home'),
    path('products/', include('products.frontend_urls')),
    path('users/', include('users.frontend_urls')),
    path('orders/', include('orders.frontend_urls')),
]

# Add this to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
