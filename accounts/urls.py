from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/addresses/', views.address_list, name='address_list'),
    path('profile/addresses/add/', views.add_address, name='add_address'),
    path('profile/addresses/<int:pk>/edit/', views.edit_address, name='edit_address'),
    path('profile/addresses/<int:pk>/delete/', views.delete_address, name='delete_address'),
    path('profile/addresses/<int:pk>/set-default/', views.set_default_address, name='set_default_address'),
]
