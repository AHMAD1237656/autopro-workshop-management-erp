from django.urls import path
from .views import (
    account_create_view,
    account_list_view,
    account_statement_view,
    expense_create_view,
    expense_list_view,
)

urlpatterns = [
    path('', account_list_view, name='account_list'),
    path('expenses/', expense_list_view, name='expense_list'),
    path('expenses/create/', expense_create_view, name='expense_create'),
    path('create/', account_create_view, name='account_create'),
    path('statement/<int:account_id>/', account_statement_view, name='account_statement'),
]