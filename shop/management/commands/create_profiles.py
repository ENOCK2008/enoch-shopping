# shop/management/commands/create_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Profile

class Command(BaseCommand):
    help = 'Create profiles for all users'

    def handle(self, *args, **kwargs):
        User = get_user_model()  # Get the custom user model
        for user in User.objects.all():
            Profile.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS('Profiles created successfully.'))
