from django.dispatch import receiver

from pretix.base.signals import register_invoice_renderers

@receiver(register_invoice_renderers, dispatch_uid="output_custom")
def register_invoice_renderers(sender, **kwargs):
    from .invoice import FSPInvoiceRenderer
    return FSPInvoiceRenderer