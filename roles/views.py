from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Role, UserProfile
from django.contrib import messages

@login_required
def role_matrix_view(request):
    roles = Role.objects.all()
    profiles = UserProfile.objects.select_related('user', 'role').all()
    
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        role_id = request.POST.get('role_id')
        
        profile = UserProfile.objects.get(user_id=user_id)
        if role_id:
            profile.role_id = role_id
        else:
            profile.role = None
        profile.save()
        messages.success(request, f"Role for user '{profile.user.username}' updated successfully!")
        return redirect('role_matrix')

    return render(request, 'roles/matrix.html', {
        'roles': roles,
        'profiles': profiles
    })