from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class PluginApp(AppConfig):
    name = 'preitx_fsp_invoice_renderer'
    verbose_name = 'FSP Rechnungserzeuger'

    class PretixPluginMeta:
        name = ugettext_lazy('FSP Rechnungserzeuger')
        author = 'Felix Gohla'
        description = ugettext_lazy('Das Plugin erlaubt es, Rechnungen zu erstellen, die gleiche Produkte zusammenfassen.')
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'preitx_fsp_invoice_renderer.PluginApp'
