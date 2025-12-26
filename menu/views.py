from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, MenuItem

def home(request):
    categories = Category.objects.filter(is_active=True)[:6]
    featured_items = MenuItem.objects.filter(is_available=True)[:8]
    
    context = {
        'categories': categories,
        'featured_items': featured_items,
    }
    return render(request, 'menu/home.html', context)

def menu_list(request):
    categories = Category.objects.filter(is_active=True)
    
    # Filter options
    is_vegetarian = request.GET.get('vegetarian')
    is_vegan = request.GET.get('vegan')
    is_gluten_free = request.GET.get('gluten_free')
    
    # Base queryset
    menu_items = MenuItem.objects.filter(is_available=True)
    
    # Apply filters
    if is_vegetarian:
        menu_items = menu_items.filter(is_vegetarian=True)
    if is_vegan:
        menu_items = menu_items.filter(is_vegan=True)
    if is_gluten_free:
        menu_items = menu_items.filter(is_gluten_free=True)
    
    context = {
        'categories': categories,
        'menu_items': menu_items,
        'is_vegetarian': is_vegetarian,
        'is_vegan': is_vegan,
        'is_gluten_free': is_gluten_free,
    }
    return render(request, 'menu/menu_list.html', context)

def category_detail(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    menu_items = MenuItem.objects.filter(category=category, is_available=True)
    
    context = {
        'category': category,
        'menu_items': menu_items,
    }
    return render(request, 'menu/category_detail.html', context)

def menu_item_detail(request, item_slug):
    menu_item = get_object_or_404(MenuItem, slug=item_slug, is_available=True)
    related_items = MenuItem.objects.filter(category=menu_item.category).exclude(id=menu_item.id)[:4]
    
    context = {
        'menu_item': menu_item,
        'related_items': related_items,
    }
    return render(request, 'menu/menu_item_detail.html', context)

def search_menu(request):
    query = request.GET.get('q', '')
    
    if query:
        menu_items = MenuItem.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(is_available=True)
    else:
        menu_items = MenuItem.objects.none()
    
    context = {
        'menu_items': menu_items,
        'query': query,
    }
    return render(request, 'menu/search_results.html', context)
