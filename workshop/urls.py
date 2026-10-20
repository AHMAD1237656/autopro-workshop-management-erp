from django.urls import path
from .views import job_card_list_view, job_card_create_view

urlpatterns = [
    path('jobs/', job_card_list_view, name='job_card_list'),
    path('jobs/create/', job_card_create_view, name='job_card_create'),
]