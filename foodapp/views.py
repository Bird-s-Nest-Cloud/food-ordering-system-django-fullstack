from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count, Prefetch
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from datetime import datetime, timedelta

from .models import Customer, MenuItem, Order, OrderItem, Delivery, Expense, Category
from .serializers import CustomerSerializer, MenuItemSerializer, OrderSerializer, OrderItemSerializer, DeliverySerializer, ExpenseSerializer
from .forms import CustomerForm, OrderForm, OrderItemFormSet

# Helper functions for role-based access
def is_manager_or_admin(user):
    return user.is_authenticated and (user.is_manager() or user.is_admin())

def is_admin(user):
    return user.is_authenticated and user.is_admin()

# API ViewSets
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    
    def create(self, request, *args, **kwargs):
        items_data = request.data.pop('items', [])
        serializer = self.get_serializer(data=request.data, context={'items_data': items_data})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

# Frontend Views
def home(request):
    return render(request, 'foodapp/home.html')

# Customer Module Views
def menu(request):
    categories = Category.objects.prefetch_related(
        Prefetch('menu_items', queryset=MenuItem.objects.filter(is_available=True))
    ).all()
    menu_items_no_category = MenuItem.objects.filter(category__isnull=True, is_available=True)
    return render(request, 'foodapp/menu.html', {
        'categories': categories,
        'menu_items_no_category': menu_items_no_category
    })

def place_order(request):
    if request.method == 'POST':
        customer_form = CustomerForm(request.POST)
        if customer_form.is_valid():
            customer = customer_form.save()
            order = Order.objects.create(customer=customer, status='new')
            
            # Process order items
            menu_items = request.POST.getlist('menu_item')
            quantities = request.POST.getlist('quantity')
            
            for i in range(len(menu_items)):
                if int(quantities[i]) > 0:
                    menu_item = MenuItem.objects.get(id=menu_items[i])
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantities[i]
                    )
            
            return redirect('order_confirmation', order_id=order.id)
    else:
        customer_form = CustomerForm()
        # Get all categories with their available menu items
        categories = Category.objects.prefetch_related(
            Prefetch('menu_items', queryset=MenuItem.objects.filter(is_available=True))
        ).all()
        # Also get menu items without category
        menu_items_no_category = MenuItem.objects.filter(category__isnull=True, is_available=True)
    
    return render(request, 'foodapp/place_order.html', {
        'customer_form': customer_form,
        'categories': categories,
        'menu_items_no_category': menu_items_no_category
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'foodapp/order_confirmation.html', {'order': order})

# Manager Module Views
@login_required
@user_passes_test(is_manager_or_admin, login_url='login')
def manager_dashboard(request):
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    
    new_orders = Order.objects.filter(status='new').order_by('-created_at')
    kitchen_orders = Order.objects.filter(status='kitchen').order_by('-created_at')
    ready_orders = Order.objects.filter(status='ready').order_by('-created_at')
    # Show only today's delivered orders
    delivered_orders = Order.objects.filter(
        status='delivered',
        created_at__date=today
    ).order_by('-created_at')
    cancelled_orders = Order.objects.filter(status='cancelled').order_by('-created_at')
    
    return render(request, 'foodapp/manager_dashboard.html', {
        'new_orders': new_orders,
        'kitchen_orders': kitchen_orders,
        'ready_orders': ready_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders
    })

@login_required
@user_passes_test(is_manager_or_admin, login_url='login')
@csrf_exempt
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in [status[0] for status in Order.STATUS_CHOICES]:
            order.status = new_status
            order.save()
            
            # If status is delivered, create delivery record
            if new_status == 'delivered':
                delivery_person = data.get('delivery_person', 'Unknown')
                Delivery.objects.create(
                    order=order,
                    delivery_person=delivery_person,
                    delivered_at=timezone.now()
                )
            
            return JsonResponse({'success': True})
        
    return JsonResponse({'success': False})

# Owner Module Views
@login_required
@user_passes_test(is_admin, login_url='login')
def owner_dashboard(request):
    # Get date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get orders in date range
    orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
    expenses = Expense.objects.all().order_by('-date')
    total_expenses_amount = sum(expense.amount for expense in expenses)
    # Calculate daily revenue
    daily_revenue = []
    current_date = start_date
    while current_date <= end_date:
        day_orders = orders.filter(created_at__date=current_date)
        day_total = sum(order.total_price for order in day_orders)
        daily_revenue.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'revenue': float(day_total)
        })
        current_date += timedelta(days=1)
    
    # Get expenses in date range - use a more explicit query
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    
    # Debug information
    print(f"Date range: {start_date} to {end_date}")
    print(f"Number of expenses found: {expenses.count()}")
    
    # Try multiple methods to calculate total expenses
    total_expenses_aggregate = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses_manual = sum(float(expense.amount) for expense in expenses)
    
    print(f"Total expenses (aggregate): {total_expenses_aggregate}")
    print(f"Total expenses (manual): {total_expenses_manual}")
    
    # Use the manual calculation to be safe
    total_expenses = total_expenses_manual
    
    # Calculate total revenue
    total_revenue = sum(order.total_price for order in orders)
    
    # Calculate net profit
    net_profit = total_revenue - total_expenses_amount
    
    # Get order count
    order_count = orders.count()
    
    # Get popular items
    popular_items = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'menu_item__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'order_count': order_count,
        'daily_revenue': json.dumps(daily_revenue),
        'popular_items': popular_items,
        'total_expenses_amount' : total_expenses_amount,
        'expenses' : expenses,
    }
    
    return render(request, 'foodapp/owner_dashboard.html', context)

@login_required
@user_passes_test(is_admin, login_url='login')
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    total_amount = sum(expense.amount for expense in expenses)
    return render(request, 'foodapp/expense_list.html', {
        'expenses': expenses,
        'total_amount': total_amount
    })

@login_required
@user_passes_test(is_admin, login_url='login')
def add_expense(request):
    if request.method == 'POST':
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        
        if description and amount:
            # Create expense with today's date explicitly
            Expense.objects.create(
                description=description,
                amount=float(amount),
                date=timezone.now().date()
            )
            return redirect('expense_list')
    
    return render(request, 'foodapp/add_expense.html')
