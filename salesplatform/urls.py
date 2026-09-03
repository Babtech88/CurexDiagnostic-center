from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('salesplatform.storefront_urls')),
    path('order/', include('orders.urls')),

    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('customers/', include('customers.urls')),
    path('whatsapp-bot/', include('whatsapp_bot.urls')),
    path('results/', include('results.urls')),
    path('content/', include('sitecontent.urls')),
    path('articles/', include('sitecontent.public_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
