from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        STAFF = 'STAFF', _('Staff')
        DELIVERY = 'DELIVERY', _('Delivery Person')
        CUSTOMER = 'CUSTOMER', _('Customer')
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_manager(self):
        return self.role == self.Role.MANAGER
    
    def is_staff_member(self):
        return self.role == self.Role.STAFF
    
    def is_delivery_person(self):
        return self.role == self.Role.DELIVERY
    
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_addresses')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.state} {self.postal_code}"
