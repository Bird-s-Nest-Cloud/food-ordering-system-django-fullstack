from django.urls import path
from . import views

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:menu_item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/delivery/', views.delivery_checkout, name='delivery_checkout'),
    path('checkout/pickup/', views.pickup_checkout, name='pickup_checkout'),
    path('checkout/complete/', views.checkout_complete, name='checkout_complete'),
    
    # Order URLs
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
]
