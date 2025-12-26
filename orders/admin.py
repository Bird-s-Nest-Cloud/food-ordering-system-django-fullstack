from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderStatusUpdate

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'total_price', 'updated_at')
    inlines = [CartItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'variant', 'quantity', 'unit_price', 'total_price', 'special_instructions')

class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 1
    readonly_fields = ('created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'customer_name', 'status', 'order_type', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'order_type', 'payment_status', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = ('order_number', 'subtotal', 'tax', 'total', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderStatusUpdateInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'order_type')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Delivery/Pickup Information', {
            'fields': ('delivery_address', 'delivery_instructions', 'pickup_time')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'payment_method')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'tax', 'delivery_fee', 'discount', 'total')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at', 'estimated_delivery_time', 'actual_delivery_time')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'variant', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'menu_item__name')

@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'updated_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'notes')
