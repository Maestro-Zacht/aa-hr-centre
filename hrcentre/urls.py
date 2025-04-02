from django.urls import path

from . import views

app_name = 'hrcentre'

urlpatterns = [
    path('', views.index, name='index'),
    path('setup/corporation/<int:corp_id>/', views.corp_view, name='corp_view'),
    path('setup/alliance/<int:alliance_id>/', views.alliance_view, name='alliance_view'),
]
