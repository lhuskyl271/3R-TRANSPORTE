from django.apps import AppConfig

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'

    def ready(self):
        """
        This method is called only after Django's app registry is fully loaded.
        It is the correct place for model imports and startup code.
        """
        # Import models here to avoid the AppRegistryNotReady error
        from django.contrib.auth.models import User

        # Create the superuser only if it doesn't already exist
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                "admin", 
                "admin@example.com", 
                "nitram"
            )