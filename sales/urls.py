from django.urls import path
from .views import pos_terminal_view, sales_history_view

urlpatterns = [
    path('pos/', pos_terminal_view, name='pos_terminal'),
    path('history/', sales_history_view, name='sales_history'),
]