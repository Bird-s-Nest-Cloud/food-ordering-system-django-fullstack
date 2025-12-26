from django.db import models
from django.conf import settings
from django.utils import timezone

class Expense(models.Model):
    class ExpenseCategory(models.TextChoices):
        INGREDIENTS = 'INGREDIENTS', 'Ingredients'
        STAFF = 'STAFF', 'Staff Wages'
        UTILITIES = 'UTILITIES', 'Utilities'
        RENT = 'RENT', 'Rent'
        EQUIPMENT = 'EQUIPMENT', 'Equipment'
        MARKETING = 'MARKETING', 'Marketing'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        OTHER = 'OTHER', 'Other'
    
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount}৳"

class DailySummary(models.Model):
    date = models.DateField(unique=True)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Daily Summaries'
    
    def __str__(self):
        return f"Summary for {self.date}"

class CategorySales(models.Model):
    summary = models.ForeignKey(DailySummary, on_delete=models.CASCADE, related_name='category_sales')
    category_name = models.CharField(max_length=100)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    items_sold = models.PositiveIntegerField()
    
    class Meta:
        verbose_name_plural = 'Category Sales'
    
    def __str__(self):
        return f"{self.category_name} - {self.summary.date}"

class PopularItem(models.Model):
    summary = models.ForeignKey(DailySummary, on_delete=models.CASCADE, related_name='popular_items')
    item_name = models.CharField(max_length=100)
    quantity_sold = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.item_name} - {self.summary.date}"
