from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'

class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        import shop.signals
