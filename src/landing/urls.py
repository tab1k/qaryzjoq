from django.urls import path

from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.index, name='index'),
    path('thanks/', views.thanks, name='thanks'),
    path('api/b24/extract-promo/', views.extract_promo_webhook, name='extract_promo_webhook'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
]
