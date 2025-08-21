from django.apps import AppConfig
# Importamos el error específico que queremos atrapar
from django.db.utils import ProgrammingError

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'

    def ready(self):
        """
        Este método se ejecuta cuando las apps de Django están listas.
        """
        try:
            # Se importa el modelo aquí para evitar errores de carga
            from django.contrib.auth.models import User

            # Se crea el superusuario solo si no existe
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(
                    "admin",
                    "admin@example.com",
                    "nitram"
                )
        except ProgrammingError:
            # Este error ocurre si las tablas aún no han sido creadas (durante migrate)
            # Simplemente lo ignoramos para permitir que la migración continúe.
            pass