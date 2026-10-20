from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


@ensure_csrf_cookie
def user_login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('dashboard_home')
        messages.error(request, 'Invalid username or password.')

    return render(request, 'auth/login.html', {'next': request.GET.get('next', '')})


@require_POST
def user_logout_view(request):
    logout(request)
    return redirect('login')
