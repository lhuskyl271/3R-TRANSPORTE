# ventas/management/commands/create_initial_superuser.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Crea un superusuario inicial si no existe uno con el nombre de usuario "admin"'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.SUCCESS('Creando superusuario "admin"...'))
            User.objects.create_superuser('admin', 'admin@example.com', 'nitram')
            self.stdout.write(self.style.SUCCESS('¡Superusuario "admin" creado exitosamente!'))
        else:
            self.stdout.write(self.style.WARNING('El superusuario "admin" ya existe.'))