from django.contrib import admin
from .models import Category, MenuItem, Ingredient, MenuItemIngredient, MenuItemVariant

class MenuItemIngredientInline(admin.TabularInline):
    model = MenuItemIngredient
    extra = 1

class MenuItemVariantInline(admin.TabularInline):
    model = MenuItemVariant
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_available')
    list_filter = ('category', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_available')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MenuItemIngredientInline, MenuItemVariantInline]

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_allergen')
    list_filter = ('is_allergen',)
    search_fields = ('name',)

@admin.register(MenuItemIngredient)
class MenuItemIngredientAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'ingredient', 'quantity')
    list_filter = ('ingredient', 'menu_item')
    search_fields = ('menu_item__name', 'ingredient__name')

@admin.register(MenuItemVariant)
class MenuItemVariantAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'name', 'price_adjustment')
    list_filter = ('menu_item',)
    search_fields = ('menu_item__name', 'name')
