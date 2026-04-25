from django.urls import path
from  . import views

urlpatterns = [
    path('', views.selector_sede, name= 'selector_sede'),
    
]