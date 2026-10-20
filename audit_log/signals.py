from django.db.models.signals import post_save
from django.dispatch import receiver

from payments.models import PaymentVoucher
from sales.models import Sale
from workshop.models import JobCard

from .utils import get_audit_context, log_activity


@receiver(post_save, sender=JobCard, dispatch_uid='audit_log_job_card_created')
@receiver(post_save, sender=Sale, dispatch_uid='audit_log_sale_created')
@receiver(post_save, sender=PaymentVoucher, dispatch_uid='audit_log_payment_voucher_created')
def record_created_business_event(sender, instance, created, **kwargs):
    if not created:
        return

    user, ip_address = get_audit_context()
    if user is None and isinstance(instance, Sale):
        user = instance.cashier

    log_activity(
        user=user,
        action='Created',
        model_name=sender._meta.label,
        object_repr=instance,
        ip_address=ip_address,
    )
