from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import InvoiceProfile
from sales.models import Sale
from workshop.models import JobCard


@login_required
def invoice_detail_view(request, invoice_no):
    profile = InvoiceProfile.objects.filter(pk=1).first()
    # Check if this invoice number belongs to a retail POS sale
    sale = Sale.objects.filter(sale_invoice_no=invoice_no).prefetch_related('items__part').first()
    if sale:
        return render(request, 'invoices/print_pos_invoice.html', {
            'sale': sale,
            'items': sale.items.all(),
            'invoice_profile': profile,
            'auto_print': request.GET.get('print') == '1',
        })

    # Otherwise, resolve it as a Workshop Job Card repair invoice
    job = get_object_or_404(
        JobCard.objects.select_related('vehicle', 'assigned_mechanic').prefetch_related('parts_used__part'),
        job_number=invoice_no
    )
    return render(request, 'invoices/print_workshop_invoice.html', {
        'job': job,
        'parts': job.parts_used.all(),
        'invoice_profile': profile,
    })


@login_required
def invoice_settings_view(request):
    profile, _ = InvoiceProfile.objects.get_or_create(pk=1)
    if request.method == 'POST':
        legal_title = request.POST.get('legal_title', '').strip()
        placement = request.POST.get('logo_placement')
        layout = request.POST.get('layout')
        logo = request.FILES.get('logo')

        if not legal_title:
            messages.error(request, 'Enter the legal business title.')
            return render(request, 'invoices/settings.html', {'profile': profile})
        if placement not in dict(InvoiceProfile.LOGO_PLACEMENTS):
            messages.error(request, 'Select a valid logo placement.')
            return render(request, 'invoices/settings.html', {'profile': profile})
        if layout not in dict(InvoiceProfile.LAYOUTS):
            messages.error(request, 'Select a valid invoice layout.')
            return render(request, 'invoices/settings.html', {'profile': profile})
        if logo:
            if logo.size > 2 * 1024 * 1024:
                messages.error(request, 'The logo file must not exceed 2 MB.')
                return render(request, 'invoices/settings.html', {'profile': profile})
            extension = logo.name.rsplit('.', 1)[-1].lower() if '.' in logo.name else ''
            signature = logo.read(12)
            logo.seek(0)
            valid_signatures = {
                'png': signature.startswith(b'\x89PNG\r\n\x1a\n'),
                'jpg': signature.startswith(b'\xff\xd8\xff'),
                'jpeg': signature.startswith(b'\xff\xd8\xff'),
                'webp': signature.startswith(b'RIFF') and signature[8:12] == b'WEBP',
            }
            if not valid_signatures.get(extension, False):
                messages.error(request, 'Upload a valid PNG, JPEG, or WebP image file.')
                return render(request, 'invoices/settings.html', {'profile': profile})

        profile.legal_title = legal_title
        profile.contact_numbers = request.POST.get('contact_numbers', '').strip()
        profile.tax_id = request.POST.get('tax_id', '').strip()
        profile.physical_address = request.POST.get('physical_address', '').strip()
        profile.footer_terms = request.POST.get('footer_terms', '').strip()
        profile.logo_placement = placement
        profile.layout = layout
        if logo:
            profile.logo = logo
        elif request.POST.get('remove_logo') == 'on':
            profile.logo = ''
        profile.save()
        messages.success(request, 'Invoice settings have been saved.')
        return redirect('invoice_settings')

    return render(request, 'invoices/settings.html', {'profile': profile})