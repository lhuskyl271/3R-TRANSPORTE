from django.apps import AppConfig
from django.db.utils import ProgrammingError

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'

    def ready(self):
        """
        Este método se ejecuta cuando las apps de Django están listas.
        """
        # Aunque este código funciona, es la causa de la advertencia de inicio.
        # Es mejor crear el superusuario manualmente una vez con:
        # python manage.py createsuperuser
        try:
            from django.contrib.auth.models import User

            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser(
                    "admin",
                    "admin@example.com",
                    "nitram"
                )
        except ProgrammingError:
            # Este error ocurre si las tablas aún no han sido creadas (durante migrate)
            pass
