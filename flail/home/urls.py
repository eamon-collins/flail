from django.urls import path
from .views import HomeView
from django.contrib.auth.decorators import login_required
urlpatterns = [
    path('', HomeView.as_view(), name='flail-home')
]