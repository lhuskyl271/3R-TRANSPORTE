# ventas/apps.py
from django.apps import AppConfig

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'

# No es necesario tener el método ready() aquí.
# También puedes eliminar la clase MyAppConfig si no la estás usando.