from django.urls import path

from . import views

app_name = 'hrcentre'

urlpatterns = [
    path('', views.index, name='index'),
]
