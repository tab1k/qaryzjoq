from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from landing.acme import acme_challenge

urlpatterns = [
    path('.well-known/acme-challenge/<str:token>', acme_challenge),
    path('admin/', admin.site.urls),
    path('', include('landing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
