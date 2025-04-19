from django.urls import path

from . import views

app_name = 'hrcentre'

urlpatterns = [
    path('', views.index, name='index'),
    path('setups/corporation/<int:corp_id>/', views.CorporationAuditListView.as_view(), name='corp_view'),
    path('setups/alliance/<int:alliance_id>/', views.AllianceAuditListView.as_view(), name='alliance_view'),
    path('users/<int:user_id>/', views.user_view, name='user_view'),
    path('users/<int:user_id>/labels/', views.user_labels_view, name='user_labels'),
    path('users/<int:user_id>/notes/', views.user_notes_view, name='user_notes'),
]
