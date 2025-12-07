from django.urls import path
from . import views

app_name = 'connect'

urlpatterns = [
    path('', views.connect_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
]
