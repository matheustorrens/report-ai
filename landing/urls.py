from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('privacidad/', views.privacy_policy, name='privacy_policy'),
    path('terminos/', views.terms_of_service, name='terms_of_service'),
]
