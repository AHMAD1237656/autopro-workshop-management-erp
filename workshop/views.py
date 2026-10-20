from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import JobCard, Vehicle
from django.contrib.auth.models import User
import uuid

@login_required
def job_card_list_view(request):
    jobs = JobCard.objects.select_related('vehicle', 'assigned_mechanic').prefetch_related('parts_used').all().order_by('-created_at')
    return render(request, 'workshop/list.html', {'jobs': jobs})

@login_required
def job_card_create_view(request):
    if request.method == "POST":
        reg_no = request.POST.get('registration_number').upper()
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        make = request.POST.get('make')
        model_name = request.POST.get('model_name')
        year = request.POST.get('year')
        mileage = request.POST.get('mileage')
        complaint = request.POST.get('complaint_description')
        mechanic_id = request.POST.get('mechanic_id')

        vehicle, _ = Vehicle.objects.get_or_create(
            registration_number=reg_no,
            defaults={
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'make': make,
                'model_name': model_name,
                'year': year,
                'mileage': mileage
            }
        )

        job_no = f"JC-{uuid.uuid4().hex[:6].upper()}"
        mechanic = User.objects.filter(id=mechanic_id).first() if mechanic_id else None

        JobCard.objects.create(
            job_number=job_no,
            vehicle=vehicle,
            assigned_mechanic=mechanic,
            complaint_description=complaint,
            status='IN_PROGRESS'
        )
        messages.success(request, f"New repair job '{job_no}' successfully open ho gaya!")
        return redirect('job_card_list')

    mechanics = User.objects.all()
    return render(request, 'workshop/form.html', {'mechanics': mechanics})