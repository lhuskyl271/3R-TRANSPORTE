# my_app/management/commands/setup_data.py
from django.core.management.base import BaseCommand
from my_app.models import SomeModel

class Command(BaseCommand):
    help = 'Initializes necessary data for the app.'

    def handle(self, *args, **options):
        if not SomeModel.objects.exists():
            self.stdout.write(self.style.SUCCESS('Creating initial data...'))
            # Your data creation logic here
        else:
            self.stdout.write('Data already initialized.')