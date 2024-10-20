from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Message

# Create your views here.


def show_message(request):
    now = timezone.now()
    ten_minutes_ago = now - timedelta(minutes=5)
    messages = Message.objects.filter(timestamp__gte=ten_minutes_ago).order_by('-timestamp')
    # messages = Message.objects.order_by('-timestamp')[:10]
    return render(request, 'messages.html', {'messages': messages})