from django.urls import path

from .views import reports_view


urlpatterns = [
    path('', reports_view, name='reports'),
]
