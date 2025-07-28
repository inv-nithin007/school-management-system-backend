from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Create admin user with username admin and password admin123'

    def handle(self, *args, **options):
        # Check if admin user already exists
        if User.objects.filter(username='admin').exists():
            self.stdout.write(
                self.style.WARNING('Admin user already exists!')
            )
            return

        # Create admin user
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@school.com',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )

        # Create user profile for admin
        UserProfile.objects.create(
            user=admin_user,
            role='admin'
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Admin user created successfully!\n'
                'Username: admin\n'
                'Password: admin123\n'
                'Role: admin'
            )
        )