
from django.urls import path
from .views import *
urlpatterns = [
    path('user/login/',LoginView.as_view() , name='login'),
    path('user/register/',RegisterView.as_view() , name='Register'),
    path('user/profile/',ProfileView.as_view() , name='Profile'),
    
]