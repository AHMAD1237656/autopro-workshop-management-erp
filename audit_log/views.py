from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import ActivityLog


@login_required
def activity_list_view(request):
    paginator = Paginator(
        ActivityLog.objects.select_related('user').all(),
        50,
    )
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'audit_log/activity_list.html', {'page': page})
