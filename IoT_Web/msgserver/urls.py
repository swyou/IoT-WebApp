from django.urls import path
from .views import show_message

urlpatterns = [
    path('', show_message, name='show_message'),
]