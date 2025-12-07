from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('interface/', views.chat_interface, name='interface'),
]
