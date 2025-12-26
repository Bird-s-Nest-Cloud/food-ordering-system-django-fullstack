from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API router
router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'menu', views.MenuItemViewSet)
router.register(r'deliveries', views.DeliveryViewSet)
router.register(r'expenses', views.ExpenseViewSet)

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Frontend URLs
    path('', views.home, name='home'),
    
    # Customer Module
    path('menu/', views.menu, name='menu'),
    path('order/', views.place_order, name='place_order'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # Manager Module
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/order/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    
    # Owner Module
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/expenses/', views.expense_list, name='expense_list'),
    path('owner/expenses/add/', views.add_expense, name='add_expense'),
]
