from django.apps import AppConfig


class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'
    
from django.contrib.auth.models import User

class MiAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mi_app'  # Asegúrate de que coincida con el nombre de tu app

    def ready(self):
        # Crear superusuario automáticamente si no existe
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin", 
                "admin@example.com", 
                "nitram"
            )
