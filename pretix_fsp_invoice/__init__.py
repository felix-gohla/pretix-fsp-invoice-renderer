from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class PluginApp(AppConfig):
    name = 'pretix_fsp_invoice'
    verbose_name = 'FSP Rechnungsplugin'

    class PretixPluginMeta:
        name = ugettext_lazy('FSP Rechnungsplugin')
        author = 'Felix Gohla'
        description = ugettext_lazy('Das Plugin erlaubt es, Rechnungen zu erstellen, die gleiche Produkte zusammenfassen.')
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_fsp_invoice.PluginApp'
