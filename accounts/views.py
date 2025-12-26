from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserChangeForm, DeliveryAddressForm
from .models import DeliveryAddress

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    addresses = DeliveryAddress.objects.filter(user=request.user)
    return render(request, 'accounts/profile.html', {'addresses': addresses})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def address_list(request):
    addresses = DeliveryAddress.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})

@login_required
def add_address(request):
    if request.method == 'POST':
        form = DeliveryAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset any other default
            if address.is_default:
                DeliveryAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
                
            address.save()
            messages.success(request, 'Address added successfully.')
            return redirect('address_list')
    else:
        form = DeliveryAddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add Address'})

@login_required
def edit_address(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = DeliveryAddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            
            # If this is set as default, unset any other default
            if address.is_default:
                DeliveryAddress.objects.filter(user=request.user, is_default=True).exclude(pk=pk).update(is_default=False)
                
            address.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('address_list')
    else:
        form = DeliveryAddressForm(instance=address)
    
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})

@login_required
def delete_address(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully.')
        return redirect('address_list')
    
    return render(request, 'accounts/delete_address.html', {'address': address})

@login_required
def set_default_address(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    
    # Unset any current default
    DeliveryAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
    
    # Set the new default
    address.is_default = True
    address.save()
    
    messages.success(request, 'Default address updated.')
    return redirect('address_list')
