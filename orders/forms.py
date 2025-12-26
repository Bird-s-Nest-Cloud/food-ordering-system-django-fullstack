from django import forms
from .models import Order, CartItem

class AddToCartForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity', 'special_instructions']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special instructions?'}),
        }

class DeliveryOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'delivery_address', 'delivery_instructions',
            'payment_method'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

class PickupOrderForm(forms.ModelForm):
    pickup_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        help_text='Select your preferred pickup time'
    )
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'pickup_time', 'payment_method'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
