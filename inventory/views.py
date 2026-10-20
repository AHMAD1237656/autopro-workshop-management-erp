from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SparePart, Category

@login_required
def part_list_view(request):
    parts = SparePart.objects.select_related('category').all().order_by('-created_at')
    categories = Category.objects.all()
    
    query = request.GET.get('q')
    if query:
        parts = parts.filter(name__icontains=query) | parts.filter(part_number__icontains=query)

    return render(request, 'inventory/list.html', {
        'parts': parts,
        'categories': categories,
        'search_query': query or ''
    })

@login_required
def part_create_view(request):
    if request.method == "POST":
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        part_number = request.POST.get('part_number')
        brand = request.POST.get('brand')
        compatible_vehicles = request.POST.get('compatible_vehicles')
        shelf_location = request.POST.get('shelf_location')
        cost_price = request.POST.get('cost_price')
        selling_price = request.POST.get('selling_price')
        stock_quantity = request.POST.get('stock_quantity')
        min_stock_alert = request.POST.get('min_stock_alert')

        category = get_object_or_404(Category, id=category_id)
        SparePart.objects.create(
            category=category,
            name=name,
            part_number=part_number,
            brand=brand,
            compatible_vehicles=compatible_vehicles,
            shelf_location=shelf_location,
            cost_price=cost_price,
            selling_price=selling_price,
            stock_quantity=stock_quantity,
            min_stock_alert=min_stock_alert
        )
        messages.success(request, f"Spare part '{name}' inventory mein add ho gaya!")
        return redirect('part_list')

    categories = Category.objects.all()
    if not categories.exists():
        Category.objects.create(name="Engine Components", description="Pistons, plugs, belts, filters")
        Category.objects.create(name="Brakes & Suspension", description="Pads, shoes, shocks")
        categories = Category.objects.all()

    return render(request, 'inventory/form.html', {'categories': categories})