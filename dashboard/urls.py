from django.urls import path
from . import views

urlpatterns = [
    # Manager Dashboard
    path('', views.manager_dashboard, name='manager_dashboard'),
    path('orders/', views.order_management, name='order_management'),
    path('orders/<str:order_number>/', views.order_detail, name='manager_order_detail'),
    path('orders/<str:order_number>/update/', views.update_order_status, name='update_order_status'),
    path('orders/<str:order_number>/assign/', views.assign_order, name='assign_order'),
    
    # Owner Dashboard
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/reports/', views.sales_reports, name='sales_reports'),
    path('owner/reports/daily/', views.daily_report, name='daily_report'),
    path('owner/reports/weekly/', views.weekly_report, name='weekly_report'),
    path('owner/reports/monthly/', views.monthly_report, name='monthly_report'),
    path('owner/reports/yearly/', views.yearly_report, name='yearly_report'),
    path('owner/reports/custom/', views.custom_report, name='custom_report'),
    
    # Expenses
    path('owner/expenses/', views.expense_list, name='expense_list'),
    path('owner/expenses/add/', views.add_expense, name='add_expense'),
    path('owner/expenses/<int:pk>/edit/', views.edit_expense, name='edit_expense'),
    path('owner/expenses/<int:pk>/delete/', views.delete_expense, name='delete_expense'),
    
    # API endpoints for charts
    path('api/sales-data/', views.sales_data, name='sales_data'),
    path('api/category-sales/', views.category_sales, name='category_sales'),
    path('api/expense-breakdown/', views.expense_breakdown, name='expense_breakdown'),
]
