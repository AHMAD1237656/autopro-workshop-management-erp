from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ShowroomVehicle

@login_required
def vehicle_list_view(request):
    vehicles = ShowroomVehicle.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    status_filter = request.GET.get('status')

    if query:
        vehicles = vehicles.filter(title__icontains=query) | vehicles.filter(vin_number__icontains=query)
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)

    return render(request, 'showroom/list.html', {
        'vehicles': vehicles,
        'search_query': query or '',
        'selected_status': status_filter or ''
    })

@login_required
def vehicle_create_view(request):
    if request.method == "POST":
        vin_number = request.POST.get('vin_number').upper()
        engine_number = request.POST.get('engine_number').upper()
        title = request.POST.get('title')
        make = request.POST.get('make')
        model_name = request.POST.get('model_name')
        year = request.POST.get('year')
        mileage = request.POST.get('mileage')
        color = request.POST.get('color')
        condition = request.POST.get('condition')
        purchase_cost = request.POST.get('purchase_cost')
        selling_price = request.POST.get('selling_price')
        registration_status = request.POST.get('registration_status')

        ShowroomVehicle.objects.create(
            vin_number=vin_number,
            engine_number=engine_number,
            title=title,
            make=make,
            model_name=model_name,
            year=year,
            mileage=mileage,
            color=color,
            condition=condition,
            purchase_cost=purchase_cost,
            selling_price=selling_price,
            registration_status=registration_status,
            status='AVAILABLE'
        )
        messages.success(request, f"Vehicle '{title}' successfully added to showroom inventory!")
        return redirect('vehicle_list')

    return render(request, 'showroom/form.html')