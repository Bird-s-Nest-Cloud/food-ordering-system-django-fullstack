from django.contrib import admin
from .models import Expense, DailySummary, CategorySales, PopularItem

class CategorySalesInline(admin.TabularInline):
    model = CategorySales
    extra = 1

class PopularItemInline(admin.TabularInline):
    model = PopularItem
    extra = 1

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'category', 'date', 'created_by')
    list_filter = ('category', 'date', 'created_by')
    search_fields = ('title', 'description')
    date_hierarchy = 'date'

@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_orders', 'total_revenue', 'total_expenses', 'net_profit')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    inlines = [CategorySalesInline, PopularItemInline]

@admin.register(CategorySales)
class CategorySalesAdmin(admin.ModelAdmin):
    list_display = ('summary', 'category_name', 'total_sales', 'items_sold')
    list_filter = ('summary__date', 'category_name')
    search_fields = ('category_name',)

@admin.register(PopularItem)
class PopularItemAdmin(admin.ModelAdmin):
    list_display = ('summary', 'item_name', 'quantity_sold', 'revenue')
    list_filter = ('summary__date',)
    search_fields = ('item_name',)
