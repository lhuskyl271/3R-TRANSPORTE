from django.apps import AppConfig

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'

    def ready(self):
        """
        This method is called when Django's app registry is fully populated.
        It's the correct place to import models and run setup code, like
        creating a superuser.
        """
        # Import models here to avoid AppRegistryNotReady error
        from django.contrib.auth.models import User

        # Create superuser automatically only if it doesn't exist
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin", 
                "admin@example.com", 
                "nitram"
            )