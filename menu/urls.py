from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('menu/item/<slug:item_slug>/', views.menu_item_detail, name='menu_item_detail'),
    path('search/', views.search_menu, name='search_menu'),
]
