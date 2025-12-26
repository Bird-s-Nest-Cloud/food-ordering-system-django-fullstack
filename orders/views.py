import uuid
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from .models import Cart, CartItem, Order, OrderItem, OrderStatusUpdate
from .forms import AddToCartForm, DeliveryOrderForm, PickupOrderForm
from menu.models import MenuItem, MenuItemVariant
from accounts.models import DeliveryAddress

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    return None

@login_required
def cart_detail(request):
    cart = get_or_create_cart(request)
    context = {'cart': cart}
    return render(request, 'orders/cart_detail.html', context)

@login_required
def add_to_cart(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)
    cart = get_or_create_cart(request)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            special_instructions = form.cleaned_data['special_instructions']
            variant_id = request.POST.get('variant')
            
            variant = None
            if variant_id:
                variant = get_object_or_404(MenuItemVariant, id=variant_id, menu_item=menu_item)
            
            # Check if this item is already in the cart
            try:
                cart_item = CartItem.objects.get(
                    cart=cart,
                    menu_item=menu_item,
                    variant=variant
                )
                cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, f'Updated quantity for {menu_item.name} in your cart.')
            except CartItem.DoesNotExist:
                CartItem.objects.create(
                    cart=cart,
                    menu_item=menu_item,
                    variant=variant,
                    quantity=quantity,
                    special_instructions=special_instructions
                )
                messages.success(request, f'Added {menu_item.name} to your cart.')
            
            return redirect('cart_detail')
    else:
        form = AddToCartForm()
    
    context = {
        'menu_item': menu_item,
        'form': form
    }
    return render(request, 'orders/add_to_cart.html', context)

@login_required
def update_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully.')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart.')
    
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart_detail')

@login_required
def clear_cart(request):
    cart = get_or_create_cart(request)
    if cart:
        cart.items.all().delete()
        messages.success(request, 'Your cart has been cleared.')
    return redirect('cart_detail')

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Your cart is empty. Please add some items before checkout.')
        return redirect('menu_list')
    
    # Get user's default delivery address if available
    default_address = DeliveryAddress.objects.filter(user=request.user, is_default=True).first()
    
    context = {
        'cart': cart,
        'default_address': default_address,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def delivery_checkout(request):
    cart = get_or_create_cart(request)
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Your cart is empty. Please add some items before checkout.')
        return redirect('menu_list')
    
    # Get user's default delivery address if available
    default_address = DeliveryAddress.objects.filter(user=request.user, is_default=True).first()
    
    initial_data = {}
    if default_address:
        initial_data = {
            'delivery_address': f"{default_address.address_line1}, {default_address.address_line2}, {default_address.city}, {default_address.state} {default_address.postal_code}",
        }
    
    # Add user information to initial data
    initial_data.update({
        'customer_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'customer_phone': request.user.phone_number,
        'customer_email': request.user.email,
    })
    
    if request.method == 'POST':
        form = DeliveryOrderForm(request.POST)
        if form.is_valid():
            return create_order(request, form, cart, Order.OrderType.DELIVERY)
    else:
        form = DeliveryOrderForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'orders/delivery_checkout.html', context)

@login_required
def pickup_checkout(request):
    cart = get_or_create_cart(request)
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Your cart is empty. Please add some items before checkout.')
        return redirect('menu_list')
    
    # Set initial pickup time to 30 minutes from now
    initial_pickup_time = timezone.now() + datetime.timedelta(minutes=30)
    
    initial_data = {
        'customer_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'customer_phone': request.user.phone_number,
        'customer_email': request.user.email,
        'pickup_time': initial_pickup_time,
    }
    
    if request.method == 'POST':
        form = PickupOrderForm(request.POST)
        if form.is_valid():
            return create_order(request, form, cart, Order.OrderType.PICKUP)
    else:
        form = PickupOrderForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'orders/pickup_checkout.html', context)

@transaction.atomic
def create_order(request, form, cart, order_type):
    # Calculate order totals
    subtotal = cart.total_price
    tax_rate = 0.08  # 8% tax rate
    tax = subtotal * tax_rate
    
    # Set delivery fee based on order type
    delivery_fee = 0
    if order_type == Order.OrderType.DELIVERY:
        delivery_fee = 2.99  # Example delivery fee
    
    total = subtotal + tax + delivery_fee
    
    # Create the order
    order = form.save(commit=False)
    order.user = request.user
    order.order_number = str(uuid.uuid4())[:8].upper()
    order.order_type = order_type
    order.subtotal = subtotal
    order.tax = tax
    order.delivery_fee = delivery_fee
    order.total = total
    order.save()
    
    # Create order items from cart items
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            menu_item=cart_item.menu_item,
            variant=cart_item.variant.name if cart_item.variant else '',
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.total_price,
            special_instructions=cart_item.special_instructions
        )
    
    # Create initial status update
    OrderStatusUpdate.objects.create(
        order=order,
        status=Order.OrderStatus.NEW,
        updated_by=request.user,
        notes='Order placed by customer'
    )
    
    # Clear the cart
    cart.items.all().delete()
    
    # Store order number in session for confirmation page
    request.session['order_number'] = order.order_number
    
    return redirect('checkout_complete')

@login_required
def checkout_complete(request):
    order_number = request.session.get('order_number')
    if not order_number:
        return redirect('home')
    
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Clear the session
    if 'order_number' in request.session:
        del request.session['order_number']
    
    context = {
        'order': order,
    }
    return render(request, 'orders/checkout_complete.html', context)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Only allow cancellation if order is new
    if order.status != Order.OrderStatus.NEW:
        messages.error(request, 'Sorry, this order cannot be cancelled.')
        return redirect('order_detail', order_number=order_number)
    
    if request.method == 'POST':
        order.status = Order.OrderStatus.CANCELLED
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status=Order.OrderStatus.CANCELLED,
            updated_by=request.user,
            notes='Order cancelled by customer'
        )
        
        messages.success(request, 'Your order has been cancelled.')
        return redirect('order_list')
    
    context = {
        'order': order,
    }
    return render(request, 'orders/cancel_order.html', context)
