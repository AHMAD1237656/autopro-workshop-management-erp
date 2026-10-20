from django.urls import path

from .views import activity_list_view


urlpatterns = [
    path('', activity_list_view, name='audit_log'),
]
