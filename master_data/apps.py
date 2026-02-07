from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MasterDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'master_data'
    verbose_name = _("Master Data")
