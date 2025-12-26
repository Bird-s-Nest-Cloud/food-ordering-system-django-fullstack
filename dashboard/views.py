import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Expense, DailySummary
from .forms import ExpenseForm, DateRangeForm, OrderStatusUpdateForm
from orders.models import Order, OrderItem, OrderStatusUpdate
from accounts.models import User
from menu.models import Category, MenuItem

@login_required
def manager_dashboard(request):
    # Check if user is a manager or admin
    if not (request.user.is_admin() or request.user.is_manager()):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get today's date
    today = timezone.now().date()
    
    # Get today's orders
    today_orders = Order.objects.filter(created_at__date=today)
    
    # Get order counts by status
    new_orders_count = today_orders.filter(status=Order.OrderStatus.NEW).count()
    preparing_orders_count = today_orders.filter(status=Order.OrderStatus.PREPARING).count()
    ready_orders_count = today_orders.filter(status=Order.OrderStatus.READY).count()
    delivered_orders_count = today_orders.filter(
        Q(status=Order.OrderStatus.DELIVERED) | Q(status=Order.OrderStatus.PICKED_UP)
    ).count()
    
    # Get total revenue for today
    today_revenue = today_orders.aggregate(total=Sum('total'))['total'] or 0
    
    # Get popular items for today
    popular_items = OrderItem.objects.filter(
        order__created_at__date=today
    ).values(
        'menu_item__name', 'menu_item__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]
    
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    context = {
        'today': today,
        'new_orders_count': new_orders_count,
        'preparing_orders_count': preparing_orders_count,
        'ready_orders_count': ready_orders_count,
        'delivered_orders_count': delivered_orders_count,
        'today_revenue': today_revenue,
        'popular_items': popular_items,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/manager_dashboard.html', context)

@login_required
def order_management(request):
    # Check if user is a manager or admin
    if not (request.user.is_admin() or request.user.is_manager()):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get orders by status
    new_orders = Order.objects.filter(status=Order.OrderStatus.NEW).order_by('-created_at')
    preparing_orders = Order.objects.filter(status=Order.OrderStatus.PREPARING).order_by('-created_at')
    ready_orders = Order.objects.filter(status=Order.OrderStatus.READY).order_by('-created_at')
    out_for_delivery_orders = Order.objects.filter(status=Order.OrderStatus.OUT_FOR_DELIVERY).order_by('-created_at')
    
    # Get staff members for assignment
    staff_members = User.objects.filter(
        Q(role=User.Role.STAFF) | Q(role=User.Role.DELIVERY)
    )
    
    context = {
        'new_orders': new_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'out_for_delivery_orders': out_for_delivery_orders,
        'staff_members': staff_members,
    }
    return render(request, 'dashboard/order_management.html', context)

@login_required
def order_detail(request, order_number):
    # Check if user is a manager or admin
    if not (request.user.is_admin() or request.user.is_manager()):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    order = get_object_or_404(Order, order_number=order_number)
    status_form = OrderStatusUpdateForm(initial={'status': order.status})
    
    # Get staff members for assignment
    staff_members = User.objects.filter(
        Q(role=User.Role.STAFF) | Q(role=User.Role.DELIVERY)
    )
    
    context = {
        'order': order,
        'status_form': status_form,
        'staff_members': staff_members,
    }
    return render(request, 'dashboard/order_detail.html', context)

@login_required
def update_order_status(request, order_number):
    # Check if user is a manager or admin
    if not (request.user.is_admin() or request.user.is_manager()):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        form = OrderStatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            notes = form.cleaned_data['notes']
            
            # Update order status
            order.status = new_status
            order.save()
            
            # Create status update record
            OrderStatusUpdate.objects.create(
                order=order,
                status=new_status,
                notes=notes,
                updated_by=request.user
            )
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
            return redirect('order_management')
    
    return redirect('manager_order_detail', order_number=order_number)

@login_required
def assign_order(request, order_number):
    # Check if user is a manager or admin
    if not (request.user.is_admin() or request.user.is_manager()):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            staff = get_object_or_404(User, id=staff_id)
            order.assigned_to = staff
            order.save()
            
            # Add note to status updates
            OrderStatusUpdate.objects.create(
                order=order,
                status=order.status,
                notes=f'Assigned to {staff.get_full_name() or staff.username}',
                updated_by=request.user
            )
            
            messages.success(request, f'Order assigned to {staff.get_full_name() or staff.username}')
        else:
            messages.error(request, 'Please select a staff member')
    
    return redirect('manager_order_detail', order_number=order_number)

@login_required
def owner_dashboard(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get today's date
    today = timezone.now().date()
    
    # Get today's summary
    today_summary = {
        'orders': Order.objects.filter(created_at__date=today).count(),
        'revenue': Order.objects.filter(created_at__date=today).aggregate(total=Sum('total'))['total'] or 0,
        'expenses': Expense.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0,
    }
    today_summary['profit'] = today_summary['revenue'] - today_summary['expenses']
    
    # Get yesterday's summary for comparison
    yesterday = today - timedelta(days=1)
    yesterday_summary = {
        'orders': Order.objects.filter(created_at__date=yesterday).count(),
        'revenue': Order.objects.filter(created_at__date=yesterday).aggregate(total=Sum('total'))['total'] or 0,
        'expenses': Expense.objects.filter(date=yesterday).aggregate(total=Sum('amount'))['total'] or 0,
    }
    yesterday_summary['profit'] = yesterday_summary['revenue'] - yesterday_summary['expenses']
    
    # Calculate percentage changes
    if yesterday_summary['orders'] > 0:
        orders_change = ((today_summary['orders'] - yesterday_summary['orders']) / yesterday_summary['orders']) * 100
    else:
        orders_change = 100 if today_summary['orders'] > 0 else 0
    
    if yesterday_summary['revenue'] > 0:
        revenue_change = ((today_summary['revenue'] - yesterday_summary['revenue']) / yesterday_summary['revenue']) * 100
    else:
        revenue_change = 100 if today_summary['revenue'] > 0 else 0
    
    if yesterday_summary['expenses'] > 0:
        expenses_change = ((today_summary['expenses'] - yesterday_summary['expenses']) / yesterday_summary['expenses']) * 100
    else:
        expenses_change = 100 if today_summary['expenses'] > 0 else 0
    
    if yesterday_summary['profit'] > 0:
        profit_change = ((today_summary['profit'] - yesterday_summary['profit']) / yesterday_summary['profit']) * 100
    else:
        profit_change = 100 if today_summary['profit'] > 0 else 0
    
    # Get popular items for today
    popular_items = OrderItem.objects.filter(
        order__created_at__date=today
    ).values(
        'menu_item__name', 'menu_item__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]
    
    # Get expense breakdown for today
    expense_breakdown = Expense.objects.filter(
        date=today
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate total expenses for percentage calculation
    total_expenses = sum(item['total'] for item in expense_breakdown)
    
    # Add percentage to each expense category
    if total_expenses > 0:
        for item in expense_breakdown:
            item['percentage'] = (item['total'] / total_expenses) * 100
    
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Get recent expenses
    recent_expenses = Expense.objects.all().order_by('-date', '-created_at')[:5]
    
    context = {
        'today': today,
        'today_summary': today_summary,
        'orders_change': orders_change,
        'revenue_change': revenue_change,
        'expenses_change': expenses_change,
        'profit_change': profit_change,
        'popular_items': popular_items,
        'expense_breakdown': expense_breakdown,
        'recent_orders': recent_orders,
        'recent_expenses': recent_expenses,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)

@login_required
def sales_reports(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    return render(request, 'dashboard/sales_reports.html')

@login_required
def daily_report(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get date from request or use today
    date_str = request.GET.get('date')
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()
    
    # Get orders for the day
    orders = Order.objects.filter(created_at__date=report_date)
    
    # Get order summary
    order_summary = {
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(total=Sum('total'))['total'] or 0,
        'average_order_value': orders.aggregate(avg=Sum('total') / Count('id'))['avg'] or 0,
    }
    
    # Get order breakdown by status
    status_breakdown = orders.values('status').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('status')
    
    # Get order breakdown by type
    type_breakdown = orders.values('order_type').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('order_type')
    
    # Get sales by category
    category_sales = OrderItem.objects.filter(
        order__created_at__date=report_date
    ).values(
        'menu_item__category__name'
    ).annotate(
        total_sales=Sum('total_price'),
        items_sold=Sum('quantity')
    ).order_by('-total_sales')
    
    # Get popular items
    popular_items = OrderItem.objects.filter(
        order__created_at__date=report_date
    ).values(
        'menu_item__name'
    ).annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-quantity_sold')[:10]
    
    # Get expenses for the day
    expenses = Expense.objects.filter(date=report_date)
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get expense breakdown
    expense_breakdown = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate net profit
    net_profit = order_summary['total_revenue'] - total_expenses
    
    context = {
        'report_date': report_date,
        'order_summary': order_summary,
        'status_breakdown': status_breakdown,
        'type_breakdown': type_breakdown,
        'category_sales': category_sales,
        'popular_items': popular_items,
        'total_expenses': total_expenses,
        'expense_breakdown': expense_breakdown,
        'net_profit': net_profit,
    }
    return render(request, 'dashboard/daily_report.html', context)

@login_required
def weekly_report(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get start and end dates for the week
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get orders for the week
    orders = Order.objects.filter(created_at__date__range=[start_of_week, end_of_week])
    
    # Get daily breakdown
    daily_breakdown = orders.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        total_orders=Count('id'),
        total_revenue=Sum('total')
    ).order_by('day')
    
    # Get weekly summary
    weekly_summary = {
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(total=Sum('total'))['total'] or 0,
        'average_order_value': orders.aggregate(avg=Sum('total') / Count('id'))['avg'] or 0,
    }
    
    # Get expenses for the week
    expenses = Expense.objects.filter(date__range=[start_of_week, end_of_week])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get daily expense breakdown
    daily_expenses = expenses.values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Calculate net profit
    net_profit = weekly_summary['total_revenue'] - total_expenses
    
    context = {
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'daily_breakdown': daily_breakdown,
        'weekly_summary': weekly_summary,
        'total_expenses': total_expenses,
        'daily_expenses': daily_expenses,
        'net_profit': net_profit,
    }
    return render(request, 'dashboard/weekly_report.html', context)

@login_required
def monthly_report(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get month and year from request or use current month
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    if month and year:
        try:
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                month = timezone.now().month
                year = timezone.now().year
        except ValueError:
            month = timezone.now().month
            year = timezone.now().year
    else:
        month = timezone.now().month
        year = timezone.now().year
    
    # Get start and end dates for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get orders for the month
    orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
    
    # Get weekly breakdown
    weekly_breakdown = orders.annotate(
        week=TruncWeek('created_at')
    ).values('week').annotate(
        total_orders=Count('id'),
        total_revenue=Sum('total')
    ).order_by('week')
    
    # Get monthly summary
    monthly_summary = {
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(total=Sum('total'))['total'] or 0,
        'average_order_value': orders.aggregate(avg=Sum('total') / Count('id'))['avg'] or 0,
    }
    
    # Get expenses for the month
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get expense breakdown by category
    expense_breakdown = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate net profit
    net_profit = monthly_summary['total_revenue'] - total_expenses
    
    context = {
        'month': month,
        'year': year,
        'start_date': start_date,
        'end_date': end_date,
        'weekly_breakdown': weekly_breakdown,
        'monthly_summary': monthly_summary,
        'total_expenses': total_expenses,
        'expense_breakdown': expense_breakdown,
        'net_profit': net_profit,
    }
    return render(request, 'dashboard/monthly_report.html', context)

@login_required
def yearly_report(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get year from request or use current year
    year = request.GET.get('year')
    
    if year:
        try:
            year = int(year)
        except ValueError:
            year = timezone.now().year
    else:
        year = timezone.now().year
    
    # Get start and end dates for the year
    start_date = datetime(year, 1, 1).date()
    end_date = datetime(year, 12, 31).date()
    
    # Get orders for the year
    orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
    
    # Get monthly breakdown
    monthly_breakdown = orders.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_orders=Count('id'),
        total_revenue=Sum('total')
    ).order_by('month')
    
    # Get yearly summary
    yearly_summary = {
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(total=Sum('total'))['total'] or 0,
        'average_order_value': orders.aggregate(avg=Sum('total') / Count('id'))['avg'] or 0,
    }
    
    # Get expenses for the year
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get monthly expense breakdown
    monthly_expenses = expenses.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Calculate net profit
    net_profit = yearly_summary['total_revenue'] - total_expenses
    
    context = {
        'year': year,
        'start_date': start_date,
        'end_date': end_date,
        'monthly_breakdown': monthly_breakdown,
        'yearly_summary': yearly_summary,
        'total_expenses': total_expenses,
        'monthly_expenses': monthly_expenses,
        'net_profit': net_profit,
    }
    return render(request, 'dashboard/yearly_report.html', context)

@login_required
def custom_report(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Get orders for the date range
            orders = Order.objects.filter(created_at__date__range=[start_date, end_date])
            
            # Get daily breakdown
            daily_breakdown = orders.annotate(
                day=TruncDay('created_at')
            ).values('day').annotate(
                total_orders=Count('id'),
                total_revenue=Sum('total')
            ).order_by('day')
            
            # Get summary
            summary = {
                'total_orders': orders.count(),
                'total_revenue': orders.aggregate(total=Sum('total'))['total'] or 0,
                'average_order_value': orders.aggregate(avg=Sum('total') / Count('id'))['avg'] or 0,
            }
            
            # Get expenses for the date range
            expenses = Expense.objects.filter(date__range=[start_date, end_date])
            total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
            
            # Get expense breakdown by category
            expense_breakdown = expenses.values('category').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            # Calculate net profit
            net_profit = summary['total_revenue'] - total_expenses
            
            context = {
                'form': form,
                'start_date': start_date,
                'end_date': end_date,
                'daily_breakdown': daily_breakdown,
                'summary': summary,
                'total_expenses': total_expenses,
                'expense_breakdown': expense_breakdown,
                'net_profit': net_profit,
            }
            return render(request, 'dashboard/custom_report.html', context)
    else:
        # Default to last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        form = DateRangeForm(initial={'start_date': start_date, 'end_date': end_date})
    
    context = {
        'form': form,
    }
    return render(request, 'dashboard/custom_report.html', context)

@login_required
def expense_list(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    expenses = Expense.objects.all().order_by('-date', '-created_at')
    
    # Pagination
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'dashboard/expense_list.html', context)

@login_required
def add_expense(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Expense added successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})
    
    context = {
        'form': form,
        'title': 'Add Expense',
    }
    return render(request, 'dashboard/expense_form.html', context)

@login_required
def edit_expense(request, pk):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'title': 'Edit Expense',
    }
    return render(request, 'dashboard/expense_form.html', context)

@login_required
def delete_expense(request, pk):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect('expense_list')
    
    context = {
        'expense': expense,
    }
    return render(request, 'dashboard/delete_expense.html', context)

@login_required
def sales_data(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Get daily sales and expenses
        daily_data = []
        
        current_date = start_date
        while current_date <= end_date:
            # Get orders for the day
            daily_revenue = Order.objects.filter(
                created_at__date=current_date
            ).aggregate(total=Sum('total'))['total'] or 0
            
            # Get expenses for the day
            daily_expenses = Expense.objects.filter(
                date=current_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate profit
            daily_profit = daily_revenue - daily_expenses
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(daily_revenue),
                'expenses': float(daily_expenses),
                'profit': float(daily_profit)
            })
            
            current_date += timedelta(days=1)
        
        return JsonResponse({'data': daily_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def category_sales(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Get sales by category
        category_data = OrderItem.objects.filter(
            order__created_at__date__range=[start_date, end_date]
        ).values(
            'menu_item__category__name'
        ).annotate(
            total_sales=Sum('total_price'),
            items_sold=Sum('quantity')
        ).order_by('-total_sales')
        
        # Format data for chart
        chart_data = []
        for item in category_data:
            category_name = item['menu_item__category__name'] or 'Uncategorized'
            chart_data.append({
                'category': category_name,
                'sales': float(item['total_sales']),
                'items': item['items_sold']
            })
        
        return JsonResponse({'data': chart_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def expense_breakdown(request):
    # Check if user is an owner/admin
    if not request.user.is_admin():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        
        # Get expense breakdown by category
        expense_data = Expense.objects.filter(
            date__range=[start_date, end_date]
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Format data for chart
        chart_data = []
        for item in expense_data:
            chart_data.append({
                'category': item['category'],
                'amount': float(item['total'])
            })
        
        return JsonResponse({'data': chart_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
